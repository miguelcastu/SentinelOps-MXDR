"""Run the offline case-management demo. No Azure credentials or network needed."""
import argparse
import json
from pathlib import Path

from soar.demo import run_demo


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(".local/soar"))
    parser.add_argument("--risk-report", type=Path, help="Optional bounded synthetic rba report.json; no live incident input")
    args = parser.parse_args()
    risk_report = None
    if args.risk_report:
        if args.risk_report.stat().st_size > 524288:
            raise ValueError("Synthetic report exceeds the local bound")
        risk_report = json.loads(args.risk_report.read_text(encoding="utf-8"))
    report = run_demo(args.output, risk_report)
    for filename, value in (("report.synthetic.json", report), ("cases.synthetic.json", report["cases"]), ("audit.synthetic.json", report["audit"])):
        (args.output / filename).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    (args.output / "README.md").write_text("# Synthetic local SOAR execution\n\n"
        f"Cases: {report['counts']['cases']}; closed: {report['counts']['closed']}; local tickets: {report['counts']['tickets']}.\n\n"
        "Finding -> investigation -> evidence notes -> reviewer decision -> BenignPositive closure -> idempotent local ticket.\n\n"
        "Fictional reviewer approval only; no live incident or cloud operation. See report.synthetic.json and audit.synthetic.json.\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("evidence", "counts", "audit_chain_verified", "scenario_checks", "safety")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, KeyError, TypeError, OSError):
        raise SystemExit("Local SOAR stopped: invalid input, state or persistence; no cloud action attempted") from None
