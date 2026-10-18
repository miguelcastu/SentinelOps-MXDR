"""Offline reproducible demo only. No command in this CLI authenticates or sends data."""
import argparse
import hashlib
import json
from pathlib import Path

from ingestion.client import MAX_ATTEMPTS, batches
from ingestion.config import configuration
from ingestion.events import generate, normalize_many


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=24)
    parser.add_argument("--start", default="2026-10-18T10:00:00Z")
    parser.add_argument("--seed", default="demo")
    parser.add_argument("--output", type=Path, default=Path(".local/ingestion-demo"))
    args = parser.parse_args()
    source = generate(args.count, args.start, args.seed)
    payloads = batches(source)
    # Exercise the infrastructure contract offline with a deliberately fictional ID.
    configuration("/subscriptions/11111111-1111-4111-8111-111111111111/resourceGroups/rg-sentinelops-mxdr/providers/Microsoft.OperationalInsights/workspaces/law-sentinelops-mxdr-euw")
    result = {"mode": "offline-synthetic", "events": len(source), "batches": len(payloads),
              "payload_bytes": sum(map(len, payloads)), "worst_case_http_requests": len(payloads) * MAX_ATTEMPTS,
              "payload_sha256": hashlib.sha256(b"".join(payloads)).hexdigest(),
              "azure_requests": 0, "azure_ingestion_verified": False}
    args.output.mkdir(parents=True, exist_ok=True)
    for name, value in (("source.json", source), ("normalized.json", normalize_many(source)), ("report.json", result)):
        (args.output / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError):
        raise SystemExit("Offline ingestion validation failed; inspect local inputs and schema") from None
