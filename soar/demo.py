"""Reproducible fictional case workflow and bounded local failure experiments."""
from datetime import datetime, timedelta, timezone
import copy
from pathlib import Path
import tempfile

from rba.demo import dataset
from rba.engine import correlate
from soar.store import CaseStore, require


AS_OF = datetime(2026, 10, 18, 12, 25, tzinfo=timezone.utc)
RATIONALE = "Controlled fictional exercise: all source events are synthetic and no Azure attack or incident occurred. Close as a benign positive after checking event lineage."


def investigate_case(store, report):
    case_id = store.intake_report(report)[0]
    if store.case(case_id)["state"] == "New":
        store.investigate(case_id)
        store.add_note(case_id, "All seven original source-event IDs and the same-account/host/resource sequence reconcile to the fictional input dataset. Endpoint source health remains Unknown.", "evidence")
        store.add_note(case_id, "Review source health before inferring production impact. No containment action or cloud API is supported by this local workflow.", "recommendation")
    return case_id


def failure_scenarios(report):
    checks = []
    with tempfile.TemporaryDirectory(prefix="sentinelops-soar-check-") as directory:
        for scenario, state, attempts in (("transient", "Delivered", 2), ("timeout", "Failed", 3), ("permanent", "Failed", 1)):
            with CaseStore(Path(directory) / (scenario + ".sqlite3"), clock=lambda: AS_OF) as store:
                case_id = store.intake_report(report)[0]
                result = store.deliver_ticket(case_id, scenario)
                require(result["state"] == state and result["attempts"] == attempts)
                require(store.deliver_ticket(case_id, "available") == result)
                require(store.verify_audit())
                checks.append({"scenario": scenario, "state": state, "attempts": attempts, "retry_budget_persists": True, "passed": True})
        with CaseStore(Path(directory) / "gates.sqlite3", clock=lambda: AS_OF) as store:
            case_id = investigate_case(store, report)
            approval = store.request_closure(case_id, "BenignPositive", RATIONALE)
            require(store.decide(approval, False, "More investigation is required before closure.") == "Denied")
            require(store.case(case_id)["state"] == "Investigating")
            checks.append({"scenario": "reviewer-denial", "state": "Investigating", "passed": True})
            approval = store.request_closure(case_id, "BenignPositive", RATIONALE)
            store.clock = lambda: AS_OF + timedelta(minutes=16)
            require(store.decide(approval, True, "Attempted review after the approval deadline.") == "Expired")
            require(store.case(case_id)["state"] == "Investigating")
            checks.append({"scenario": "expired-approval", "state": "Investigating", "passed": True})
            changed = copy.deepcopy(report)
            changed["findings"][0]["priority"] = "Medium"
            try:
                store.intake_report(changed)
            except ValueError:
                checks.append({"scenario": "conflicting-replay", "rejected": True, "passed": True})
            else:
                raise ValueError("Conflicting replay was not rejected")
    return checks


def run_demo(output, risk_report=None):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    report = risk_report or correlate(dataset())
    require(isinstance(report.get("findings"), list) and len(report["findings"]) == 1, "The bounded demo requires exactly one synthetic finding")
    with CaseStore(output / "case-store.sqlite3", clock=lambda: AS_OF) as store:
        case_id = investigate_case(store, report)
        case = store.case(case_id)
        if case["state"] == "Investigating":
            approval = store.request_closure(case_id, "BenignPositive", RATIONALE)
            require(store.decide(approval, True, "Fictional reviewer checked event IDs, synthetic labeling and lack of real impact.") == "Approved")
        require(store.case(case_id)["state"] == "Closed")
        delivery = store.deliver_ticket(case_id, "transient")
        require(delivery["state"] == "Delivered")
        require(store.intake_report(report) == [case_id])
        cases, audit = store.cases(), store.audit()
        require(store.verify_audit())
        return {
            "schema_version": "1.0", "evidence": "synthetic-local-soar", "customer": "Atlas Financial",
            "as_of": AS_OF.isoformat().replace("+00:00", "Z"), "cases": cases,
            "counts": {"cases": len(cases), "closed": sum(c["state"] == "Closed" for c in cases),
                       "tickets": store.db.execute("SELECT COUNT(*) FROM tickets").fetchone()[0], "audit_events": len(audit)},
            "audit_chain_verified": True, "audit": audit, "scenario_checks": failure_scenarios(report),
            "safety": {"network_calls": 0, "azure_changes": 0, "sentinel_incidents_created": 0, "containment_actions": 0},
            "limitations": ["Local synthetic roles and decisions do not authenticate humans.",
                            "Audit chaining detects ordinary corruption, not a privileged database rewrite.",
                            "Timeouts and retries are deterministic local connector simulations, not a verified remote transport.",
                            "No Azure incident, automation rule, Logic App, SaaS ticket or containment was created."]}
