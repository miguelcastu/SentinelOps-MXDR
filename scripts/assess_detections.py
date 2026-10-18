"""Explain synthetic triage outcomes using the restricted filters; never execute Kusto."""
import json

from scripts.validate_detection import DETECTIONS, ROOT, parse_predicates, validate_rule


def assess(cases):
    results = {key: {"synthetic_events": 0, "benign_matches": 0, "suspicious_matches": 0,
                     "nonmatches": 0, "missed_suspicious": 0} for key in DETECTIONS}
    for case in cases:
        key = case["detection"]
        rule = validate_rule(detection=key)
        seconds, predicates = parse_predicates(rule["properties"]["query"], key)
        event = {"OperationNameValue": case["operation"], "ActivityStatusValue": case["status"]}
        matched = -seconds <= case["offset"] <= 0 and all(event[k].casefold() in values for k, values in predicates)
        if case["verdict"] not in ("benign", "suspicious") or case.get("synthetic") is not True:
            raise ValueError("Assessment requires explicitly judged synthetic fixtures")
        result = results[key]
        result["synthetic_events"] += 1
        if matched:
            result["benign_matches" if case["verdict"] == "benign" else "suspicious_matches"] += 1
        else:
            result["nonmatches"] += 1
            result["missed_suspicious"] += case["verdict"] == "suspicious"
    return {"mode": "offline-synthetic-filter-assessment", "real_false_positive_rate": None,
            "kusto_executed": False, "detections": results}


if __name__ == "__main__":
    cases = json.loads((ROOT / "tests/fixtures/detection_triage.json").read_text(encoding="utf-8"))
    print(json.dumps(assess(cases), indent=2))
