"""Offline quality checks (no Azure credentials required)."""
from pathlib import Path
import unittest

BASE = Path(__file__).resolve().parents[1]

class TestRepo(unittest.TestCase):
    def test_query_files(self):
        files = list((BASE / "hunting").glob("*.kql"))
        self.assertGreaterEqual(len(files), 6)
        for path in files:
            content = path.read_text(encoding="utf-8")
            self.assertIn("AzureActivity", content)
            self.assertIn("TimeGenerated", content)
            self.assertIn("ago(24h)", content)

    def test_docs(self):
        for path in ("README.md", "docs/onboarding/azure-activity.md", "docs/validation/first-ingestion.md", "docs/troubleshooting/azure-policy-remediation.md"):
            self.assertTrue((BASE/path).exists(), path)

if __name__ == "__main__":
    unittest.main()
