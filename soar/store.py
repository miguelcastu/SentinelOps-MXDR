"""Durable fictional case management with scoped decisions and an audited outbox.

The local roles/decisions demonstrate workflow gates; they do not authenticate
people. SQLite and the audit chain are not a security boundary against a person
who can rewrite the database. No HTTP, shell, Azure SDK or containment primitive
is used here.
"""
import hashlib
import json
import math
from pathlib import Path
import re
import sqlite3
from datetime import datetime, timedelta, timezone

from rba.model import instant, load_policy, signal


ACTORS = {"lab-analyst": "analyst", "lab-reviewer": "reviewer"}
CLASSIFICATIONS = {"BenignPositive", "FalsePositive", "TruePositive", "Undetermined"}
FINDING_FIELDS = {
    "finding_id", "evidence", "entity_id", "rule", "first_detected", "first_score",
    "peak_score", "current_score", "priority", "confidence", "confidence_is_calibrated",
    "health_limitations", "chain_event_ids", "evidence_chain", "techniques",
    "investigation_steps", "sentinel_incident_created",
}
GENESIS = "0" * 64


def require(value, message="Invalid local SOAR contract; no input values logged"):
    if not value:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def bounded_text(value, maximum=2000):
    require(isinstance(value, str) and 8 <= len(value) <= maximum)
    require(not any(ord(c) < 32 and c not in "\n\t" for c in value))
    return value


def validate_finding(finding):
    require(isinstance(finding, dict) and set(finding) == FINDING_FIELDS)
    require(finding["evidence"] == "synthetic" and finding["rule"] == "AF-RBA-001")
    require(finding["sentinel_incident_created"] is False and finding["confidence_is_calibrated"] is False)
    require(isinstance(finding["finding_id"], str) and re.fullmatch(r"synthetic-finding-[0-9a-f]{32}", finding["finding_id"]))
    require(isinstance(finding["entity_id"], str) and re.fullmatch(r"synthetic-user-[0-9]{2}", finding["entity_id"]))
    require(finding["priority"] in {"High", "Medium", "Low", "Informational"})
    require(finding["confidence"] in {"Low", "Medium"})
    instant(finding["first_detected"])
    for key in ("first_score", "peak_score", "current_score"):
        score = finding[key]
        require(type(score) in (int, float) and math.isfinite(score) and 0 <= score <= 100)
    require(isinstance(finding["evidence_chain"], list) and 7 <= len(finding["evidence_chain"]) <= 32)
    policy = load_policy()
    events = [signal(event, policy) for event in finding["evidence_chain"]]
    require([e["event_id"] for e in events] == finding["chain_event_ids"])
    require(len({e["event_id"] for e in events}) == len(events))
    require(len({e["source_event_id"] for e in events}) == len(events))
    require(all(e["actor"] == finding["entity_id"] for e in events))
    require(all(instant(a["time"]) < instant(b["time"]) for a, b in zip(events, events[1:])))
    require([e["kind"] for e in events] == ["authentication_failure"] * 3 + ["authentication_success", "rbac_assignment", "diagnostic_change", "endpoint_execution"])
    require(events[0]["host"] == events[3]["host"] == events[-1]["host"])
    require(events[4]["resource"] == events[5]["resource"])
    require(instant(events[-1]["time"]) - instant(events[0]["time"]) <= timedelta(minutes=policy["sequence_span_minutes"]))
    require(isinstance(finding["health_limitations"], list) and set(finding["health_limitations"]) <= {e["source"] for e in events})
    techniques = sorted({t for e in events for t in policy["signals"][e["kind"]]["techniques"]})
    require(finding["techniques"] == techniques)
    require(isinstance(finding["investigation_steps"], list) and 1 <= len(finding["investigation_steps"]) <= 20)
    for step in finding["investigation_steps"]:
        bounded_text(step, 500)
    require(len(canonical(finding).encode()) <= 65536)
    return json.loads(canonical(finding))


class CaseStore:
    """Finite local case store. Every mutation and retry is transactionally audited."""

    def __init__(self, path, clock=None):
        self.db = None
        try:
            self._initialize(path, clock)
        except Exception:
            if self.db is not None:
                self.db.close()
            raise

    def _initialize(self, path, clock):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.db = sqlite3.connect(self.path, timeout=5, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS cases(
              case_id TEXT PRIMARY KEY, finding_id TEXT NOT NULL UNIQUE,
              fingerprint TEXT NOT NULL, body TEXT NOT NULL, state TEXT NOT NULL,
              revision INTEGER NOT NULL, classification TEXT, rationale TEXT);
            CREATE TABLE IF NOT EXISTS notes(
              note_id TEXT PRIMARY KEY, case_id TEXT NOT NULL REFERENCES cases,
              actor TEXT NOT NULL, category TEXT NOT NULL, text TEXT NOT NULL,
              observed_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS approvals(
              approval_id TEXT PRIMARY KEY, case_id TEXT NOT NULL REFERENCES cases,
              case_revision INTEGER NOT NULL, requester TEXT NOT NULL,
              expires_at TEXT NOT NULL, classification TEXT NOT NULL,
              rationale TEXT NOT NULL, status TEXT NOT NULL, reviewer TEXT);
            CREATE TABLE IF NOT EXISTS outbox(
              case_id TEXT PRIMARY KEY REFERENCES cases, payload_hash TEXT NOT NULL,
              attempts INTEGER NOT NULL, state TEXT NOT NULL, ticket_id TEXT);
            CREATE TABLE IF NOT EXISTS tickets(
              ticket_id TEXT PRIMARY KEY, case_id TEXT NOT NULL UNIQUE REFERENCES cases,
              payload_hash TEXT NOT NULL, body TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS audit(
              sequence INTEGER PRIMARY KEY, observed_at TEXT NOT NULL,
              case_id TEXT NOT NULL REFERENCES cases, actor TEXT NOT NULL,
              action TEXT NOT NULL, details TEXT NOT NULL,
              previous_hash TEXT NOT NULL, entry_hash TEXT NOT NULL);
            CREATE TRIGGER IF NOT EXISTS audit_no_update BEFORE UPDATE ON audit
              BEGIN SELECT RAISE(ABORT, 'audit is append-only'); END;
            CREATE TRIGGER IF NOT EXISTS audit_no_delete BEFORE DELETE ON audit
              BEGIN SELECT RAISE(ABORT, 'audit is append-only'); END;
        """)
        require(self.verify_audit(), "Local audit chain mismatch; stopped")

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.db.close()

    def _time(self):
        value = self.clock()
        require(isinstance(value, datetime) and value.tzinfo is not None)
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    def _begin(self):
        self.db.execute("BEGIN IMMEDIATE")
        require(self.verify_audit(), "Local audit chain mismatch; stopped")

    def _case(self, case_id):
        row = self.db.execute("SELECT * FROM cases WHERE case_id=?", (case_id,)).fetchone()
        require(row is not None, "Unknown local case")
        return row

    def _actor(self, actor, role):
        require(ACTORS.get(actor) == role, "Local workflow role rejected")

    def _audit(self, case_id, actor, action, details):
        previous = self.db.execute("SELECT sequence,entry_hash FROM audit ORDER BY sequence DESC LIMIT 1").fetchone()
        sequence = previous["sequence"] + 1 if previous else 1
        require(sequence <= 50000, "Local audit limit reached")
        entry = {"sequence": sequence, "observed_at": self._time(), "case_id": case_id,
                 "actor": actor, "action": action, "details": details,
                 "previous_hash": previous["entry_hash"] if previous else GENESIS}
        self.db.execute("INSERT INTO audit VALUES(?,?,?,?,?,?,?,?)",
                        (sequence, entry["observed_at"], case_id, actor, action, canonical(details), entry["previous_hash"], digest(entry)))

    def audit(self):
        return [dict(row) | {"details": json.loads(row["details"])} for row in self.db.execute("SELECT * FROM audit ORDER BY sequence")]

    def verify_audit(self):
        previous = GENESIS
        for index, row in enumerate(self.db.execute("SELECT * FROM audit ORDER BY sequence"), 1):
            entry = dict(row)
            recorded = entry.pop("entry_hash")
            try:
                entry["details"] = json.loads(entry["details"])
            except (ValueError, TypeError):
                return False
            if entry["sequence"] != index or entry["previous_hash"] != previous or recorded != digest(entry):
                return False
            previous = recorded
        return True

    def intake_report(self, report):
        require(isinstance(report, dict) and report.get("schema_version") == "1.0")
        require(report.get("evidence") == "synthetic" and report.get("customer") == "Atlas Financial")
        require(isinstance(report.get("findings"), list) and len(report["findings"]) <= 32)
        require(isinstance(report.get("limits"), dict) and report["limits"].get("sentinel_incidents_created") == 0)
        findings = [validate_finding(f) for f in report["findings"]]
        require(len({f["finding_id"] for f in findings}) == len(findings))
        result = []
        try:
            self._begin()
            for finding in findings:
                body = canonical(finding)
                fingerprint = digest(finding)
                case_id = "lab-case-" + digest(finding["finding_id"])[:24]
                prior = self.db.execute("SELECT * FROM cases WHERE finding_id=?", (finding["finding_id"],)).fetchone()
                if prior:
                    require(prior["fingerprint"] == fingerprint and prior["body"] == body, "Conflicting finding replay rejected")
                else:
                    require(self.db.execute("SELECT COUNT(*) FROM cases").fetchone()[0] < 1000)
                    self.db.execute("INSERT INTO cases VALUES(?,?,?,?,?,?,?,?)",
                                    (case_id, finding["finding_id"], fingerprint, body, "New", 1, None, None))
                    self._audit(case_id, "local-intake", "case-created", {"finding_sha256": fingerprint, "source_event_ids": [e["source_event_id"] for e in finding["evidence_chain"]]})
                result.append(case_id)
            self.db.commit()
            return result
        except Exception:
            self.db.rollback()
            raise

    def investigate(self, case_id, actor="lab-analyst"):
        self._actor(actor, "analyst")
        try:
            self._begin()
            row = self._case(case_id)
            require(row["state"] == "New", "Case transition rejected")
            self.db.execute("UPDATE cases SET state='Investigating',revision=revision+1 WHERE case_id=?", (case_id,))
            self._audit(case_id, actor, "investigation-started", {})
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def add_note(self, case_id, text, category="investigation", actor="lab-analyst"):
        self._actor(actor, "analyst")
        bounded_text(text)
        require(category in {"investigation", "evidence", "recommendation"})
        try:
            self._begin()
            row = self._case(case_id)
            require(row["state"] == "Investigating", "Notes require an investigating case")
            require(self.db.execute("SELECT COUNT(*) FROM notes WHERE case_id=?", (case_id,)).fetchone()[0] < 200)
            note_id = "lab-note-" + digest([case_id, actor, category, text])[:24]
            if not self.db.execute("SELECT 1 FROM notes WHERE note_id=?", (note_id,)).fetchone():
                self.db.execute("INSERT INTO notes VALUES(?,?,?,?,?,?)", (note_id, case_id, actor, category, text, self._time()))
                self.db.execute("UPDATE cases SET revision=revision+1 WHERE case_id=?", (case_id,))
                self._audit(case_id, actor, "note-added", {"note_id": note_id, "category": category, "text_sha256": digest(text)})
            self.db.commit()
            return note_id
        except Exception:
            self.db.rollback()
            raise

    def request_closure(self, case_id, classification, rationale, actor="lab-analyst"):
        self._actor(actor, "analyst")
        require(classification in CLASSIFICATIONS)
        bounded_text(rationale)
        try:
            self._begin()
            row = self._case(case_id)
            require(row["state"] == "Investigating", "Closure requires investigation")
            require(self.db.execute("SELECT 1 FROM notes WHERE case_id=? AND category='evidence'", (case_id,)).fetchone() is not None, "Evidence note required before closure")
            revision = row["revision"] + 1
            approval_id = "lab-approval-" + digest([case_id, revision, classification, rationale])[:24]
            expires_at = (instant(self._time()) + timedelta(minutes=15)).isoformat().replace("+00:00", "Z")
            self.db.execute("INSERT INTO approvals VALUES(?,?,?,?,?,?,?,?,?)", (approval_id, case_id, revision, actor, expires_at, classification, rationale, "Pending", None))
            self.db.execute("UPDATE cases SET state='AwaitingApproval',revision=? WHERE case_id=?", (revision, case_id))
            self._audit(case_id, actor, "closure-requested", {"approval_id": approval_id, "case_revision": revision, "classification": classification, "rationale_sha256": digest(rationale), "expires_at": expires_at})
            self.db.commit()
            return approval_id
        except Exception:
            self.db.rollback()
            raise

    def decide(self, approval_id, approved, comment, actor="lab-reviewer"):
        self._actor(actor, "reviewer")
        require(type(approved) is bool)
        bounded_text(comment)
        try:
            self._begin()
            approval = self.db.execute("SELECT * FROM approvals WHERE approval_id=?", (approval_id,)).fetchone()
            require(approval is not None and approval["status"] == "Pending", "Decision is absent or already consumed")
            row = self._case(approval["case_id"])
            require(actor != approval["requester"] and row["state"] == "AwaitingApproval" and row["revision"] == approval["case_revision"], "Decision does not match current case revision")
            expired = instant(self._time()) >= instant(approval["expires_at"])
            status = "Expired" if expired else "Approved" if approved else "Denied"
            self.db.execute("UPDATE approvals SET status=?,reviewer=? WHERE approval_id=?", (status, actor, approval_id))
            self.db.execute("UPDATE cases SET state=?,revision=revision+1,classification=?,rationale=? WHERE case_id=?",
                            ("Closed" if status == "Approved" else "Investigating", approval["classification"] if status == "Approved" else None, approval["rationale"] if status == "Approved" else None, row["case_id"]))
            self._audit(row["case_id"], actor, "closure-" + status.lower(), {"approval_id": approval_id, "comment": comment, "comment_sha256": digest(comment)})
            self.db.commit()
            return status
        except Exception:
            self.db.rollback()
            raise

    def deliver_ticket(self, case_id, scenario="available"):
        """Simulated local adapter, not a general network retry facility.

        At most three attempts persist across calls/restarts. Each logical
        attempt has a two-second deadline and 0/0.25/0.5 second retry budget.
        Scenarios model timeout/transient/permanent errors without sleeping.
        Transactionally co-locating outbox and simulated ticket prevents the
        unresolvable real distributed-system 'accepted then disconnected' gap.
        """
        require(scenario in {"available", "transient", "timeout", "permanent"})
        try:
            self._begin()
            row = self._case(case_id)
            payload = {"case_id": case_id, "finding_id": row["finding_id"], "evidence": "synthetic", "title": "Fictional Atlas Financial investigation", "finding_sha256": row["fingerprint"]}
            payload_hash = digest(payload)
            task = self.db.execute("SELECT * FROM outbox WHERE case_id=?", (case_id,)).fetchone()
            if task:
                require(task["payload_hash"] == payload_hash)
                if task["state"] == "Delivered":
                    self.db.commit()
                    return {"state": "Delivered", "attempts": task["attempts"], "ticket_id": task["ticket_id"]}
                if task["state"] == "Failed":
                    self.db.commit()
                    return {"state": "Failed", "attempts": task["attempts"], "ticket_id": None}
                attempts = task["attempts"]
            else:
                attempts = 0
                self.db.execute("INSERT INTO outbox VALUES(?,?,0,'Pending',NULL)", (case_id, payload_hash))
            while attempts < 3:
                attempts += 1
                failure = "timeout" if scenario == "timeout" else "permanent" if scenario == "permanent" else "transient" if scenario == "transient" and attempts == 1 else None
                self.db.execute("UPDATE outbox SET attempts=? WHERE case_id=?", (attempts, case_id))
                self._audit(case_id, "local-ticket-adapter", "ticket-attempt", {"attempt": attempts, "deadline_seconds": 2, "backoff_seconds": [0, .25, .5][attempts - 1], "outcome": failure or "accepted"})
                if failure:
                    if failure == "permanent" or attempts == 3:
                        self.db.execute("UPDATE outbox SET state='Failed' WHERE case_id=?", (case_id,))
                        self._audit(case_id, "local-ticket-adapter", "ticket-dead-lettered", {"attempts": attempts, "reason": failure})
                        self.db.commit()
                        return {"state": "Failed", "attempts": attempts, "ticket_id": None}
                    continue
                ticket_id = "lab-ticket-" + digest(case_id)[:24]
                self.db.execute("INSERT INTO tickets VALUES(?,?,?,?)", (ticket_id, case_id, payload_hash, canonical(payload)))
                self.db.execute("UPDATE outbox SET state='Delivered',ticket_id=? WHERE case_id=?", (ticket_id, case_id))
                self._audit(case_id, "local-ticket-adapter", "ticket-delivered", {"ticket_id": ticket_id, "attempts": attempts, "payload_sha256": payload_hash})
                self.db.commit()
                return {"state": "Delivered", "attempts": attempts, "ticket_id": ticket_id}
        except Exception:
            self.db.rollback()
            raise

    def case(self, case_id):
        row = dict(self._case(case_id))
        finding = json.loads(row.pop("body"))
        row["finding"] = finding
        row["evidence"] = "synthetic-local-case"
        row["entities"] = [{"type": "Account", "id": finding["entity_id"]}] + [
            {"type": key, "id": value} for key, value in sorted({(key, e[key]) for e in finding["evidence_chain"] for key in ("host", "source_ip", "resource") if e[key] is not None})]
        row["enrichment"] = {"source": "fictional local context", "customer": "Atlas Financial", "owner": "Fictional Atlas SOC", "asset_scope": "lab-only", "risk": {"score": finding["peak_score"], "priority": finding["priority"], "confidence": finding["confidence"], "health_limitations": finding["health_limitations"]}, "recommended_actions": finding["investigation_steps"], "containment": "Human-led investigation only; no executable containment adapter"}
        row["notes"] = [dict(n) for n in self.db.execute("SELECT * FROM notes WHERE case_id=? ORDER BY observed_at,note_id", (case_id,))]
        row["approvals"] = [dict(a) for a in self.db.execute("SELECT * FROM approvals WHERE case_id=? ORDER BY case_revision", (case_id,))]
        task = self.db.execute("SELECT * FROM outbox WHERE case_id=?", (case_id,)).fetchone()
        row["ticket_delivery"] = dict(task) if task else None
        return row

    def cases(self):
        return [self.case(row["case_id"]) for row in self.db.execute("SELECT case_id FROM cases ORDER BY case_id")]
