"""Default offline demo; opt-in CI collection uses only existing read permissions."""
import argparse
import json
import os
from pathlib import Path

from platform_health.demo import baseline, scenarios
from platform_health.engine import report, require
from platform_health.render import markdown, write_report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--collect-ci", action="store_true")
    mode.add_argument("--snapshot", type=Path)
    parser.add_argument("--as-of", help="Re-evaluation timestamp for imported aggregates only")
    parser.add_argument("--output", type=Path, default=Path(".local/platform-health"))
    args = parser.parse_args()
    require(not args.as_of or args.snapshot is not None)
    if args.collect_ci:
        from platform_health.collect import collect
        value = report(collect())
    elif args.snapshot:
        require(args.snapshot.stat().st_size <= 131_072)
        snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
        snapshot["evidence"] = "external-aggregate"
        from datetime import datetime, timezone
        value = report(snapshot, args.as_of or datetime.now(timezone.utc).isoformat())
    else:
        from platform_health.demo import NOW
        value = report(baseline(), NOW)
        value["fault_injection"] = []
        for scenario in scenarios():
            checked = report(scenario["snapshot"], NOW)
            target = next((s for s in checked["sources"] if s["source_id"] == scenario["target"]), None)
            target = target or next(c for c in checked["checks"] if c["id"] == scenario["target"])
            require(target["state"] == scenario["expected"])
            value["fault_injection"].append({"scenario": scenario["scenario"], "state": target["state"], "expected": scenario["expected"]})
    write_report(value, args.output)
    if args.collect_ci and os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as summary:
            summary.write(markdown(value))
    # A sanitized aggregate report can be recovered from job logs without paid artifact storage.
    print(json.dumps(dict(value, fault_scenarios=len(value.get("fault_injection", []))), sort_keys=True))
    return 2 if args.collect_ci and any(c["state"] == "Misconfigured" for c in value["checks"]) else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, TypeError, KeyError, StopIteration):
        raise SystemExit("Health check stopped: invalid evidence, target or authentication; no changes attempted") from None
