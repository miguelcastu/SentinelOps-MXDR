"""Authorized create/update of one fixed disabled AZ-DET-002 rule via CI OIDC."""
import json
import os
import tempfile
from pathlib import Path

from scripts.azure_guard import az_json, context, rule_url
from scripts.validate_detection import DETECTIONS, require, validate_rule

DETECTION = "AZ-DET-002"
CONFIG = DETECTIONS[DETECTION]


def verify(current, expected_id):
    require(current.get("id", "").lower() == expected_id.lower(), "Cloud resource ID mismatch")
    require(current.get("type", "").lower() == "microsoft.securityinsights/alertrules", "Unauthorized resource type")
    require(current.get("kind") == "Scheduled", "Existing resource kind mismatch")
    properties = current.get("properties", {})
    require(properties.get("displayName") == CONFIG["name"], "Existing resource name mismatch")
    require(properties.get("enabled") is False, "Stop: target must remain disabled")


def deploy():
    body = validate_rule(detection=DETECTION)
    require(os.environ.get("SENTINEL_AZ_DET_002_APPROVED") == "true", "AZ-DET-002 requires its own deployment approval")
    workspace_id = context("deploy-additional-detection.yml")
    workspace = az_json("rest", "--method", "get", "--url", f"https://management.azure.com{workspace_id}?api-version=2025-02-01")
    require(workspace.get("id", "").lower() == workspace_id.lower(), "Workspace ID mismatch")
    require(workspace.get("location", "").lower() == "westeurope", "Workspace location mismatch")
    url = rule_url(workspace_id, CONFIG["resource_uuid"])
    resource_id = url.removeprefix("https://management.azure.com").split("?", 1)[0]
    # Listing must succeed before creation; an inaccessible target is not absence.
    listing = az_json("rest", "--method", "get", "--url", url.rsplit("/", 1)[0] + "?api-version=2025-09-01")
    require(isinstance(listing.get("value"), list) and not listing.get("nextLink"),
            "Expected a complete rule inventory; no partial inventory or blind upsert")
    matches = [item for item in listing["value"] if
               item.get("name", "").lower() == CONFIG["resource_uuid"] or
               item.get("properties", {}).get("displayName", "").strip().casefold() == CONFIG["name"].casefold()]
    require(len(matches) <= 1, "Duplicate detection or conflicting target; stop for review")
    headers = ["If-None-Match=*"]
    payload = body
    if matches:
        verify(matches[0], resource_id)
        require(isinstance(matches[0].get("etag"), str) and bool(matches[0]["etag"]), "Existing etag required")
        headers = [f"If-Match={matches[0]['etag']}"]
        payload = dict(body, etag=matches[0]["etag"])
    with tempfile.TemporaryDirectory(prefix="sentinelops-new-rule-") as directory:
        path = Path(directory) / "disabled-rule.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        response = az_json("rest", "--method", "put", "--url", url,
                           "--headers", *headers, "--body", "@" + str(path))
    verify(response, resource_id)
    persisted = az_json("rest", "--method", "get", "--url", url)
    verify(persisted, resource_id)
    for key, value in body["properties"].items():
        require(persisted["properties"].get(key) == value, f"Persisted property mismatch: {key}")
    print("PASS: Azure REST confirms AZ-DET-002 at its fixed resource ID, enabled=false, PT15M/PT1H")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as stream:
            stream.write("AZ-DET-002: persisted disabled definition verified by Azure REST. No raw telemetry published.\n")


if __name__ == "__main__":
    try:
        deploy()
    except (ValueError, OSError) as exc:
        raise SystemExit(f"Deployment stopped: {exc}") from None
