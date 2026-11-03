"""Run the entire local lab and open .local/lab/index.html; no cloud mode."""
import argparse
import json
from pathlib import Path
from lab.run import run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(".local/lab"))
    parser.add_argument("--bundle", action="store_true", help="Create a local portable source/demo ZIP, never publish")
    args = parser.parse_args()
    report = run(args.output)
    if args.bundle:
        from lab.release import bundle
        result = bundle(args.output)
        print(json.dumps(result, sort_keys=True))
    print(json.dumps({"evidence": report["evidence"], "dashboard": str(args.output / "index.html"),
                      "completion": report["completion"], "risk_findings": report["risk"]["counts"]["findings"],
                      "soar": report["soar"]["counts"], "safety": report["safety"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, TypeError):
        raise SystemExit("Integrated lab stopped: invalid local input, state or artifact. No Azure operation attempted.") from None
