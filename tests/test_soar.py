"""State, persistence, lineage, approvals and failure budgets of local SOAR."""
import copy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

from rba.demo import dataset
from rba.engine import correlate
from soar.demo import AS_OF, RATIONALE, investigate_case, run_demo
from soar.store import CaseStore


class TestLocalSOAR(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name) / "cases.sqlite3"
        self.store = CaseStore(self.path, clock=lambda: AS_OF)
        self.addCleanup(self.store.db.close)
        self.report = correlate(dataset())

    def test_intake_replay_survives_reopen_and_preserves_original_lineage(self):
        ids = self.store.intake_report(self.report)
        count = len(self.store.audit())
        with CaseStore(self.path, clock=lambda: AS_OF) as reopened:
            self.assertEqual(reopened.intake_report(self.report), ids)
            self.assertEqual(len(reopened.audit()), count)
            case = reopened.case(ids[0])
            self.assertEqual(case["finding"], self.report["findings"][0])
            self.assertEqual(case["enrichment"]["risk"]["confidence"], "Low")
            self.assertIn("synthetic-endpoint", case["enrichment"]["risk"]["health_limitations"])
            self.assertEqual(case["state"], "New")
            self.assertTrue(reopened.verify_audit())

    def test_conflicting_replay_rolls_back_without_editing_prior_case(self):
        case_id = self.store.intake_report(self.report)[0]
        original = self.store.case(case_id)
        conflicting = copy.deepcopy(self.report)
        conflicting["findings"][0]["peak_score"] -= 1
        with self.assertRaises(ValueError):
            self.store.intake_report(conflicting)
        self.assertEqual(self.store.case(case_id), original)
        self.assertEqual(len(self.store.audit()), 1)

    def test_live_or_broken_lineage_input_cannot_create_cases(self):
        mutations = [
            lambda report: report.update(evidence="actual-azure"),
            lambda report: report["findings"][0].update(sentinel_incident_created=True),
            lambda report: report["findings"][0]["evidence_chain"][0].update(synthetic=False),
            lambda report: report["findings"][0]["evidence_chain"][-1].update(host="lab-auth-09"),
            lambda report: report["findings"][0]["evidence_chain"][5].update(resource="lab-resource-other"),
            lambda report: report["findings"][0].update(peak_score=float("nan")),
            lambda report: report["findings"][0].update(techniques=["T0000"]),
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutations.index(mutation)):
                report = copy.deepcopy(self.report)
                mutation(report)
                with self.assertRaises(ValueError):
                    self.store.intake_report(report)
        self.assertEqual(self.store.cases(), [])
        self.assertEqual(self.store.audit(), [])

    def test_closure_requires_investigation_evidence_and_separate_reviewer(self):
        case_id = self.store.intake_report(self.report)[0]
        with self.assertRaises(ValueError):
            self.store.request_closure(case_id, "BenignPositive", RATIONALE)
        self.store.investigate(case_id)
        with self.assertRaises(ValueError):
            self.store.request_closure(case_id, "BenignPositive", RATIONALE)
        self.store.add_note(case_id, "Synthetic original event IDs were checked; no actual Azure event exists.", "evidence")
        approval = self.store.request_closure(case_id, "BenignPositive", RATIONALE)
        with self.assertRaises(ValueError):
            self.store.decide(approval, True, "This analyst cannot self-approve the closure.", actor="lab-analyst")
        with self.assertRaises(ValueError):
            self.store.add_note(case_id, "Changing evidence while a decision is pending must be rejected.", "evidence")
        self.assertEqual(self.store.decide(approval, True, "Fictional independent reviewer checked the synthetic evidence."), "Approved")
        case = self.store.case(case_id)
        self.assertEqual((case["state"], case["classification"]), ("Closed", "BenignPositive"))
        with self.assertRaises(ValueError):
            self.store.decide(approval, True, "The completed approval cannot be reused.")
        with self.assertRaises(ValueError):
            self.store.investigate(case_id)

    def test_expired_or_denied_decision_returns_to_investigation(self):
        case_id = investigate_case(self.store, self.report)
        first = self.store.request_closure(case_id, "BenignPositive", RATIONALE)
        self.assertEqual(self.store.decide(first, False, "Fictional review requires more supporting context."), "Denied")
        self.assertEqual(self.store.case(case_id)["state"], "Investigating")
        second = self.store.request_closure(case_id, "BenignPositive", RATIONALE)
        self.store.clock = lambda: AS_OF + timedelta(minutes=15)
        self.assertEqual(self.store.decide(second, True, "The exact expiry boundary has been reached."), "Expired")
        case = self.store.case(case_id)
        self.assertEqual(case["state"], "Investigating")
        self.assertIsNone(case["classification"])
        self.assertEqual([a["status"] for a in case["approvals"]], ["Denied", "Expired"])

    def test_decision_is_bound_to_current_revision(self):
        case_id = investigate_case(self.store, self.report)
        approval = self.store.request_closure(case_id, "BenignPositive", RATIONALE)
        # An out-of-band writer is not trusted: stale approvals fail closed.
        self.store.db.execute("UPDATE cases SET revision=revision+1 WHERE case_id=?", (case_id,))
        with self.assertRaises(ValueError):
            self.store.decide(approval, True, "The pending approval is for an older revision.")
        self.assertEqual(self.store.case(case_id)["state"], "AwaitingApproval")

    def test_notes_are_bounded_structured_and_idempotent(self):
        case_id = investigate_case(self.store, self.report)
        text = "An additional synthetic observation is checked against source IDs."
        note_id = self.store.add_note(case_id, text, "evidence")
        before = self.store.case(case_id)
        self.assertEqual(self.store.add_note(case_id, text, "evidence"), note_id)
        self.assertEqual(self.store.case(case_id), before)
        for value in ("short", "x" * 2001, "bad\x00control character"):
            with self.assertRaises(ValueError):
                self.store.add_note(case_id, value)
        with self.assertRaises(ValueError):
            self.store.add_note(case_id, text, "execute-shell")

    def test_ticket_retry_is_bounded_and_delivery_survives_reopen(self):
        case_id = self.store.intake_report(self.report)[0]
        first = self.store.deliver_ticket(case_id, "transient")
        self.assertEqual((first["state"], first["attempts"]), ("Delivered", 2))
        audit_count = len(self.store.audit())
        with CaseStore(self.path, clock=lambda: AS_OF) as reopened:
            self.assertEqual(reopened.deliver_ticket(case_id), first)
            self.assertEqual(len(reopened.audit()), audit_count)
            self.assertEqual(reopened.db.execute("SELECT COUNT(*) FROM tickets").fetchone()[0], 1)
        attempts = [e for e in self.store.audit() if e["action"] == "ticket-attempt"]
        self.assertEqual([a["details"]["outcome"] for a in attempts], ["transient", "accepted"])
        self.assertTrue(all(a["details"]["deadline_seconds"] == 2 for a in attempts))

    def test_dead_letter_does_not_reset_retry_budget_on_restart(self):
        case_id = self.store.intake_report(self.report)[0]
        failed = self.store.deliver_ticket(case_id, "timeout")
        self.assertEqual((failed["state"], failed["attempts"]), ("Failed", 3))
        with CaseStore(self.path, clock=lambda: AS_OF) as reopened:
            self.assertEqual(reopened.deliver_ticket(case_id, "available"), failed)
            self.assertEqual(reopened.db.execute("SELECT COUNT(*) FROM tickets").fetchone()[0], 0)
        self.assertEqual(sum(e["action"] == "ticket-attempt" for e in self.store.audit()), 3)
        self.assertEqual(sum(e["action"] == "ticket-dead-lettered" for e in self.store.audit()), 1)

    def test_permanent_error_is_not_retried_and_no_unknown_adapter_can_run(self):
        case_id = self.store.intake_report(self.report)[0]
        failed = self.store.deliver_ticket(case_id, "permanent")
        self.assertEqual((failed["state"], failed["attempts"]), ("Failed", 1))
        with self.assertRaises(ValueError):
            self.store.deliver_ticket(case_id, "https://example.invalid")
        with self.assertRaises(ValueError):
            self.store.request_closure(case_id, "BlockAccount", RATIONALE)

    def test_audit_is_chained_append_only_and_corruption_blocks_future_mutation(self):
        case_id = self.store.intake_report(self.report)[0]
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.db.execute("DELETE FROM audit")
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.db.execute("UPDATE audit SET action='forged'")
        self.store.db.execute("DROP TRIGGER audit_no_update")
        self.store.db.execute("UPDATE audit SET action='forged'")
        self.assertFalse(self.store.verify_audit())
        with self.assertRaises(ValueError):
            self.store.investigate(case_id)
        self.assertEqual(self.store.case(case_id)["state"], "New")
        with self.assertRaises(ValueError):
            CaseStore(self.path, clock=lambda: AS_OF)

    def test_transaction_failure_cannot_leave_a_half_created_case(self):
        self.store.db.execute("CREATE TRIGGER deny_case_audit BEFORE INSERT ON audit BEGIN SELECT RAISE(ABORT,'injected local failure'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.intake_report(self.report)
        self.assertEqual(self.store.cases(), [])
        self.assertEqual(self.store.audit(), [])

    def test_demo_is_repeatable_and_does_not_generate_remote_effects(self):
        output = Path(self.temporary.name) / "demo"
        first = run_demo(output)
        second = run_demo(output)
        self.assertEqual(first, second)
        self.assertEqual(first["counts"], {"cases": 1, "closed": 1, "tickets": 1, "audit_events": 9})
        self.assertTrue(all(s["passed"] for s in first["scenario_checks"]))
        self.assertEqual(set(first["safety"].values()), {0})

    def test_cli_writes_separately_labeled_case_and_audit_exports(self):
        output = Path(self.temporary.name) / "cli"
        result = subprocess.run([sys.executable, "-m", "soar", "--output", str(output)], capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads((output / "report.synthetic.json").read_text(encoding="utf-8"))
        self.assertEqual(report["evidence"], "synthetic-local-soar")
        self.assertEqual(report["cases"][0]["classification"], "BenignPositive")
        audit = json.loads((output / "audit.synthetic.json").read_text(encoding="utf-8"))
        self.assertEqual(len(audit), 9)
        self.assertTrue((output / "case-store.sqlite3").exists())


if __name__ == "__main__":
    unittest.main()
