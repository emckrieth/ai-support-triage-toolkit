import unittest
import json
from pathlib import Path

from app.triage import recommend_runbook, run, sanitize_text


ROOT = Path(__file__).resolve().parents[1]


class TriageTests(unittest.TestCase):
    def test_sanitizer_masks_common_sensitive_values(self):
        text = "Email elvin@example.com from 192.168.1.44 on CHILAPTOP12345 with sess-abcd1234efgh."
        sanitized, counts = sanitize_text(text)

        self.assertIn("<EMAIL>", sanitized)
        self.assertIn("<PRIVATE_IP>", sanitized)
        self.assertIn("<HOSTNAME>", sanitized)
        self.assertIn("<SESSION_ID>", sanitized)
        self.assertGreaterEqual(counts["EMAIL"], 1)

    def test_endpoint_incident_recommends_endpoint_runbook(self):
        with (ROOT / "data" / "sample_incidents.json").open(encoding="utf-8") as handle:
            incidents = json.load(handle)
        runbooks = []
        for path in sorted((ROOT / "runbooks").glob("*.json")):
            with path.open(encoding="utf-8") as handle:
                runbooks.append(json.load(handle))

        result = recommend_runbook(incidents[1], runbooks)

        self.assertEqual(result["recommendation"]["runbook_id"], "endpoint-disk-pressure")
        self.assertGreaterEqual(result["recommendation"]["confidence"], 80)
        self.assertTrue(result["recommendation"]["baseline_results"])

    def test_run_writes_json_and_summary(self):
        output = ROOT / "output" / "test-triage-results.json"
        summary = ROOT / "output" / "test-support-summary.md"
        results = run(
            ROOT / "data" / "sample_incidents.json",
            ROOT / "runbooks",
            output,
            summary,
        )

        self.assertEqual(len(results), 3)
        self.assertTrue(output.exists())
        self.assertTrue(summary.exists())
        self.assertIn("Support Triage Summary", summary.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
