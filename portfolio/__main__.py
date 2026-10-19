"""Validate fixed REST/KQL contracts and synthetic control scenarios offline."""
import json
from pathlib import Path
from portfolio.catalog import SPECS, VERSION, validate
from portfolio.simulate import evaluate, scenarios


def main():
    digest = validate()
    results = []
    for case in scenarios():
        count = len(evaluate(case["detection"], case["events"], "2026-10-19T12:20:00Z"))
        if count != case["expected"]:
            raise ValueError("Synthetic case failed: " + case["id"])
        results.append({"id": case["id"], "matches": count, "passed": True})
    report = {"evidence": "synthetic-python-reference-model", "version": VERSION,
              "portfolio_sha256": digest, "new_definitions": len(SPECS), "cases": results,
              "kusto_executed": False, "azure_requests": 0, "measured_false_positive_rate": None,
              "limitations": ["Definition validation and reference simulation are not live KQL validation.",
                              "Legitimate administration can match; no real-data accuracy rate was measured."]}
    path = Path(".local/detection-portfolio")
    path.mkdir(parents=True, exist_ok=True)
    (path / "simulation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "cases"} | {"passed_cases": len(results)}))


if __name__ == "__main__":
    main()
