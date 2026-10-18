"""Assess false-positive exposure honestly without treating fixtures as real telemetry."""
import json
import unittest

from scripts.assess_detections import assess
from scripts.validate_detection import ROOT


class TestDetectionAssessment(unittest.TestCase):
    def test_benign_matches_and_failed_attack_coverage_gaps_are_reported(self):
        result = assess(json.loads((ROOT / "tests/fixtures/detection_triage.json").read_text()))
        self.assertIsNone(result["real_false_positive_rate"])
        self.assertFalse(result["kusto_executed"])
        for detection in result["detections"].values():
            self.assertEqual(detection, {"synthetic_events": 4, "benign_matches": 1,
                             "suspicious_matches": 1, "nonmatches": 2, "missed_suspicious": 1})

    def test_unlabeled_fixture_cannot_be_presented_as_real_false_positive_analysis(self):
        fixture = json.loads((ROOT / "tests/fixtures/detection_triage.json").read_text())[0]
        fixture["synthetic"] = False
        with self.assertRaises(ValueError):
            assess([fixture])
