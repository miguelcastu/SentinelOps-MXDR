"""Integrated evidence lineage, safe replay and standalone report boundaries."""
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from unittest.mock import patch

from lab.run import run
from lab.render import dashboard
from lab.release import bundle


class IntegratedLab(unittest.TestCase):
    def test_replay_preserves_one_case_and_never_authenticates_or_calls_network(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch("socket.create_connection", side_effect=AssertionError("Network forbidden")), patch("subprocess.run", side_effect=AssertionError("External process forbidden")):
                first = run(Path(directory))
                second = run(Path(directory))
            self.assertEqual(first, second)
            self.assertEqual(first["soar"]["counts"]["cases"], 1)
            self.assertEqual(first["soar"]["counts"]["closed"], 1)
            self.assertEqual(first["detection_controls"], 60)
            self.assertEqual(first["risk"]["counts"]["findings"], 1)
            case = first["soar"]["cases"][0]
            finding = first["risk"]["findings"][0]
            serialized = json.dumps(case)
            self.assertIn(finding["finding_id"], serialized)
            for event in finding["evidence_chain"]:
                self.assertIn(event["source_event_id"], serialized)
            self.assertEqual(first["safety"]["network_calls"], 0)
            self.assertTrue((Path(directory) / "index.html").is_file())

    def test_embedded_html_escapes_payload_and_keeps_actual_synthetic_evidence_separate(self):
        with tempfile.TemporaryDirectory() as directory:
            value = run(Path(directory))
        value["limitations"].append("</script><img src=x onerror=alert(1)>")
        html = dashboard(value)
        self.assertNotIn("</script><img", html)
        self.assertIn("\\u003c/script\\u003e", html)
        self.assertIn("not a live SOC dashboard", html)
        self.assertIn("Actual Azure evidence", html)
        self.assertNotIn('<script src=', html)
        self.assertNotIn('<link href="https:', html)

    def test_portable_bundle_ignores_unrelated_private_files_and_preserves_workflows(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "demo"
            run(output)
            (output / "secret.private.json").write_text('{"secret":"do-not-package"}', encoding="utf-8")
            result = bundle(output)
            with zipfile.ZipFile(result["artifact"]) as archive:
                self.assertNotIn("demo/secret.private.json", archive.namelist())
                self.assertIn("source/.github/workflows/validate.yml", archive.namelist())
                self.assertNotIn("demo/soar/case-store.sqlite3", archive.namelist())
                manifest = json.loads(archive.read("manifest.json"))
                for entry in manifest["files"]:
                    import hashlib
                    self.assertEqual(hashlib.sha256(archive.read(entry["path"])).hexdigest(), entry["sha256"])
