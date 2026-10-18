"""Finite REST transport. Never logs response bodies, URLs, credentials or event values."""
import json
import re
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass
from email.utils import parsedate_to_datetime

from ingestion.events import STREAM, normalize_many

MAX_BATCH_BYTES = 16_384
MAX_RUN_BYTES = 65_536
MAX_BATCH_ROWS = 25
MAX_ATTEMPTS = 3
MAX_REQUESTS = 24
MAX_WAIT_SECONDS = 10
MIN_REQUEST_INTERVAL = 1.0


class IngestionError(ValueError):
    """A sanitized error whose text is safe for CI output."""


@dataclass(frozen=True)
class Reply:
    status: int
    retry_after: str = ""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def destination(endpoint, immutable_id):
    parsed = urllib.parse.urlsplit(endpoint)
    if (parsed.scheme != "https" or parsed.username or parsed.password or parsed.port is not None or
            parsed.path not in ("", "/") or parsed.query or parsed.fragment or
            not re.fullmatch(r"[a-z0-9-]+\.westeurope-1\.ingest\.monitor\.azure\.com", parsed.hostname or "")):
        raise IngestionError("Only the approved West Europe Azure ingestion endpoint is accepted")
    if not re.fullmatch(r"dcr-[0-9a-f]{32}", immutable_id):
        raise IngestionError("Invalid DCR immutable identifier")
    return endpoint.rstrip("/") + "/dataCollectionRules/" + immutable_id + "/streams/" + STREAM + "?api-version=2023-01-01"


def encode(events):
    return json.dumps(events, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")


def batches(source_events):
    events = normalize_many(source_events)
    # Count full serialized arrays, including delimiters; validate every row before any POST.
    if len(encode(events)) > MAX_RUN_BYTES:
        raise IngestionError("Run payload exceeds the 64 KiB local safety limit")
    result, current = [], []
    for event in events:
        if len(encode([event])) > MAX_BATCH_BYTES:
            raise IngestionError("Single event exceeds the local batch limit")
        if current and (len(current) >= MAX_BATCH_ROWS or len(encode(current + [event])) > MAX_BATCH_BYTES):
            result.append(encode(current))
            current = []
        current.append(event)
    if current:
        result.append(encode(current))
    if sum(map(len, result)) > MAX_RUN_BYTES:
        raise IngestionError("Serialized batches exceed the run byte budget")
    if len(result) * MAX_ATTEMPTS > MAX_REQUESTS:
        raise IngestionError("Worst-case request count exceeds the run limit")
    return result


def rest_post(url, token, body):
    request = urllib.request.Request(url, data=body, method="POST", headers={
        "Authorization": "Bearer " + token, "Content-Type": "application/json",
        "x-ms-client-request-id": str(uuid.uuid4()),
    })
    tls = ssl.create_default_context()
    tls.minimum_version = ssl.TLSVersion.TLSv1_2
    opener = urllib.request.build_opener(NoRedirect(), urllib.request.HTTPSHandler(context=tls))
    try:
        with opener.open(request, timeout=20) as response:
            return Reply(response.status, response.headers.get("Retry-After", ""))
    except urllib.error.HTTPError as exc:
        # Never read or expose Azure response bodies or redirect destinations.
        reply = Reply(exc.code, exc.headers.get("Retry-After", ""))
        exc.close()
        return reply
    except (urllib.error.URLError, TimeoutError, OSError):
        raise IngestionError("Transport failed; acceptance is uncertain; reconcile IDs before retrying") from None


def retry_delay(value, attempt, wall_time=time.time):
    delay = 2 ** (attempt - 1)
    if value:
        try:
            delay = max(delay, float(value) if value.isdigit() else parsedate_to_datetime(value).timestamp() - wall_time())
        except (ValueError, TypeError, OverflowError):
            raise IngestionError("Invalid server retry interval; stopped") from None
    if delay > MAX_WAIT_SECONDS:
        raise IngestionError("Server retry interval exceeds the bounded run; stopped without early retry")
    return max(0, delay)


def upload(source_events, endpoint, immutable_id, token, *, approved=False,
           post=rest_post, sleep=time.sleep, monotonic=time.monotonic):
    if approved is not True:
        raise IngestionError("Explicit ingestion approval is required before network access")
    url = destination(endpoint, immutable_id)
    payloads = batches(source_events)
    if not isinstance(token, str) or not token or any(c.isspace() for c in token):
        raise IngestionError("A valid in-memory OIDC access token is required")
    requests, accepted, last_request = 0, 0, None
    for payload in payloads:
        for attempt in range(1, MAX_ATTEMPTS + 1):
            if requests >= MAX_REQUESTS:
                raise IngestionError("Request budget exhausted")
            if last_request is not None:
                sleep(max(0, MIN_REQUEST_INTERVAL - (monotonic() - last_request)))
            last_request = monotonic()
            requests += 1
            try:
                response = post(url, token, payload)
            except Exception:
                # An injected transport must follow the same no-telemetry exception boundary.
                raise IngestionError(f"Transport failed after {requests} requests and {accepted} API-accepted events; reconcile before rerun") from None
            if response.status == 204:
                accepted += len(json.loads(payload))
                break
            if response.status not in (429, 500, 502, 503, 504) or attempt == MAX_ATTEMPTS:
                raise IngestionError(f"Upload stopped (HTTP {response.status}) after {requests} requests and {accepted} API-accepted events; reconcile before rerun")
            sleep(retry_delay(response.retry_after, attempt))
    return {"api_accepted_events": accepted, "batches": len(payloads), "requests": requests,
            "payload_bytes": sum(map(len, payloads)), "destination_query_verified": False}
