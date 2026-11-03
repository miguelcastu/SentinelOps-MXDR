"""Integrate verified components without authentication, ingestion or containment."""
import hashlib
import json
from pathlib import Path

from ingestion.client import batches
from ingestion.events import generate, normalize_many
from infrastructure.preview import compare, snapshot
from platform_health.demo import NOW, baseline, scenarios as health_scenarios, ama_scenarios
from platform_health.engine import report as health_report
from platform_health.render import write_report as write_health
from portfolio.catalog import SPECS, validate
from portfolio.simulate import evaluate, scenarios as detection_scenarios
from rba.demo import dataset, scenarios as risk_scenarios
from rba.engine import correlate
from rba.render import write_report as write_risk
from scripts.validate_detection import DETECTIONS, ROOT, validate_rule
from soar.demo import run_demo


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def evidence_inventory():
    items = []
    for relative in ["evidence/detection-portfolio/deployment.sanitized.json",
                     "evidence/local-linux-ama/oidc-configuration.sanitized.json",
                     "evidence/local-linux-ama/ingestion.sanitized.json",
                     "evidence/local-linux-ama/shutdown.sanitized.json",
                     "evidence/completion/eligibility.sanitized.json",
                     "evidence/completion/baseline.sanitized.json",
                     "evidence/completion/lifecycle-start.sanitized.json",
                     "evidence/completion/lifecycle-close.sanitized.json"]:
        path = ROOT / relative
        if not path.exists():
            continue
        value = json.loads(path.read_text(encoding="utf-8"))
        items.append({"path": relative, "class": value.get("evidence", "historical-actual"),
                      "observed_at": value.get("verified_utc", value.get("observed_utc", value.get("review_date", "recorded in source"))),
                      "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    return items


def catalog():
    result = []
    for key in (*DETECTIONS, *SPECS):
        body = validate_rule(detection=key) if key in DETECTIONS else SPECS[key]
        if key in SPECS:
            from portfolio.catalog import definition
            body = definition(key)
        props = body["properties"]
        result.append({"id": key, "name": props["displayName"], "severity": props["severity"],
                       "techniques": props.get("techniques", []), "tactics": props.get("tactics", []),
                       "state": "Disabled", "source": "AzureActivity"})
    return result


def run(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    # This normalization fixture and the multi-source RBA exercise are distinct.
    raw = generate(24, "2026-10-18T11:58:00Z", "integrated-lab")
    normalized = normalize_many(raw)
    payloads = batches(raw)
    normalization = {"evidence": "synthetic-offline", "events": len(raw), "normalized": len(normalized),
                     "payload_bytes": sum(map(len, payloads)), "batches": len(payloads), "network_calls": 0,
                     "lineage_note": "Separate normalization fixture; RBA uses its own explicitly synthetic multi-source exercise through the same source adapters."}
    write_json(output / "ingestion/report.json", normalization)
    validate()
    controls = []
    for case in detection_scenarios():
        matched = len(evaluate(case["detection"], case["events"], "2026-10-19T12:20:00Z"))
        if matched != case["expected"]:
            raise ValueError("Detection control failed")
        controls.append({"id": case["id"], "matches": matched, "passed": True})
    write_json(output / "detections/controls.synthetic.json", controls)
    health = health_report(baseline(), NOW)
    health["fault_injection"] = []
    for case in health_scenarios() + ama_scenarios():
        checked = health_report(case["snapshot"], NOW)
        target = next((x for x in checked["sources"] if x["source_id"] == case["target"]), None)
        target = target or next(x for x in checked["checks"] if x["id"] == case["target"])
        if target["state"] != case["expected"]:
            raise ValueError("Health control failed")
        health["fault_injection"].append({"scenario": case["scenario"], "state": target["state"], "expected": case["expected"]})
    write_health(health, output / "health")
    data = dataset()
    risk = correlate(data)
    risk["scenario_checks"] = []
    for case in risk_scenarios():
        count = correlate(case["dataset"])["counts"]["findings"]
        if count != case["expected_findings"]:
            raise ValueError("Risk control failed")
        risk["scenario_checks"].append({"scenario": case["scenario"], "findings": count, "expected_findings": count})
    write_risk(risk, output / "risk")
    write_json(output / "risk/dataset.synthetic.json", data)
    soar = run_demo(output / "soar", risk)
    write_json(output / "soar/report.synthetic.json", soar)
    write_json(output / "soar/cases.synthetic.json", soar["cases"])
    write_json(output / "soar/audit.synthetic.json", soar["audit"])
    # The exact finding crosses the API boundary, with original seven-event lineage.
    if soar["counts"]["closed"] != len(risk["findings"]) or not soar["audit_chain_verified"]:
        raise ValueError("Integrated case acceptance failed")
    preview = compare(snapshot())
    write_json(output / "infrastructure/preview.synthetic.json", preview)
    public_evidence = evidence_inventory()
    cloud_start = ROOT / "evidence/completion/lifecycle-start.sanitized.json"
    cloud_close = ROOT / "evidence/completion/lifecycle-close.sanitized.json"
    live = False
    if cloud_start.exists() and cloud_close.exists():
        a, b = (json.loads(p.read_text(encoding="utf-8")) for p in (cloud_start, cloud_close))
        from lifecycle.contract import fingerprint
        live = (all(x.get("evidence") == "actual-azure-scheduled-lifecycle" and x.get("auth_mode") == "github-oidc" and x.get("approved_sha256") == fingerprint() and x.get("original_thirteen_rules_unchanged") is True and x.get("workspace_settings_unchanged") is True for x in (a, b))
                and a.get("mode") == "start" and b.get("mode") == "close"
                and isinstance(a.get("test_run_reference"), str) and len(a["test_run_reference"]) == 64 and a["test_run_reference"] == b.get("test_run_reference")
                and a.get("incident_created") is True and a.get("scheduled_rule_link_verified") is True and b.get("incident_status") == "Closed" and b.get("classification") == "BenignPositive" and b.get("test_rule_disabled") is True)
    value = {"schema_version": "1.0", "evidence": "offline-integrated-lab", "customer": "Atlas Financial (fictional)",
             "safety": {"network_calls": 0, "azure_mutations": 0, "live_queries": 0, "containment_actions": 0},
             "normalization": normalization, "detections": catalog(), "detection_controls": len(controls),
             "health": {"state": health["state"], "sources": health["sources"], "faults_passed": len(health["fault_injection"])},
             "risk": {"counts": risk["counts"], "findings": risk["findings"], "scenario_checks": len(risk["scenario_checks"])},
             "soar": {"counts": soar["counts"], "cases": soar["cases"], "audit_chain_verified": True, "failure_scenarios": len(soar["scenario_checks"])},
             "infrastructure": {"counts": preview["counts"], "evidence": preview["evidence"], "deployment_executed": False},
             "actual_cloud_evidence": public_evidence, "real_scheduled_lifecycle_verified": live,
             "completion": "verified-lab-release" if live else "offline-deliverables-verified-live-lifecycle-not-accepted",
             "limitations": ["This command replays synthetic/local evidence; it never refreshes Azure.",
                             "Twelve cloud detections remain disabled; no production coverage or measured false-positive rate.",
                             "Bicep compilation/comparison is not a platform ARM deployment.",
                             "Historical AMA ingestion is bounded; the local VM is stopped.",
                             "Local reviewer roles are fictional; remote authentication and SaaS delivery are not implemented."]}
    write_json(output / "report.json", value)
    from lab.render import dashboard
    (output / "index.html").write_text(dashboard(value), encoding="utf-8")
    return value
