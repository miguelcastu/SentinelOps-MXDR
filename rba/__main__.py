"""Run the synthetic correlation demo or a bounded synthetic dataset; no cloud mode."""
import argparse
import json
from pathlib import Path

from rba.demo import dataset, scenarios
from rba.engine import correlate
from rba.model import SOURCES, require
from rba.render import write_report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path)
    parser.add_argument("--as-of")
    parser.add_argument("--health-report", type=Path, help="Optional prior Phase 3 report; stale/future context becomes Unknown")
    parser.add_argument("--output", type=Path, default=Path(".local/rba"))
    args = parser.parse_args()
    if args.dataset:
        require(args.dataset.stat().st_size <= 524_288)
        data = json.loads(args.dataset.read_text(encoding="utf-8"))
    else:
        data = dataset()
    if args.health_report:
        require(args.health_report.stat().st_size <= 131_072)
        health = json.loads(args.health_report.read_text(encoding="utf-8"))
        require(isinstance(health.get("sources"), list) and len(health["sources"]) <= 32)
        require(len({s["source_id"] for s in health["sources"]}) == len(health["sources"]))
        states = {s:"Unknown" for s in sorted(SOURCES)}
        for source in health["sources"]:
            if source.get("source_id") in states:
                states[source["source_id"]] = source["state"]
        data["health"] = {"evidence":"imported-health", "observed_at":health["observed_at"], "states":states}
    result = correlate(data, args.as_of)
    if not args.dataset:
        result["scenario_checks"] = []
        for case in scenarios():
            checked = correlate(case["dataset"])
            require(checked["counts"]["findings"] == case["expected_findings"])
            result["scenario_checks"].append({"scenario":case["scenario"], "findings":checked["counts"]["findings"], "expected_findings":case["expected_findings"]})
    write_report(result, args.output)
    (args.output / "dataset.synthetic.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"evidence":result["evidence"], "counts":result["counts"], "limits":result["limits"],
                      "findings":[{"entity":f["entity_id"], "priority":f["priority"], "confidence":f["confidence"],
                                   "first_score":f["first_score"], "peak_score":f["peak_score"]} for f in result["findings"]],
                      "scenario_checks":len(result.get("scenario_checks", []))}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, TypeError, AttributeError, RecursionError):
        raise SystemExit("Risk analysis stopped: invalid bounded synthetic input; no Azure or network action was attempted") from None
