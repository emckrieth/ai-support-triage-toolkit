"""Regression coverage for missing versus zero weekly SLA attainment."""
import json
import unittest
from pathlib import Path

from app.support_ops import build_weekly_review

ROOT = Path(__file__).resolve().parents[1]


class WeeklyTrendSlaTests(unittest.TestCase):
    def review_for(self, weekly):
        report = json.loads((ROOT / "examples/support-ops-metrics.json").read_text(encoding="utf-8"))
        report["weekly"] = weekly
        return build_weekly_review(report)

    def test_zero_attainment_is_selected_over_fifty_and_pending(self):
        review = self.review_for([
            {"week": "2026-10-05", "first_response_sla_percent": 0.0},
            {"week": "2026-10-12", "first_response_sla_percent": 50.0},
            {"week": "2026-10-19", "first_response_sla_percent": None},
        ])
        self.assertIn("First response SLA dipped to 0% in the week of 2026-10-05.", review)

    def test_all_pending_weeks_do_not_generate_trend_warning(self):
        review = self.review_for([
            {"week": "2026-10-05", "first_response_sla_percent": None},
            {"week": "2026-10-12", "first_response_sla_percent": None},
        ])
        self.assertNotIn("## Trend to watch", review)

    def test_weeks_meeting_goal_do_not_generate_trend_warning(self):
        review = self.review_for([
            {"week": "2026-10-05", "first_response_sla_percent": 100.0},
            {"week": "2026-10-12", "first_response_sla_percent": 95.0},
        ])
        self.assertNotIn("## Trend to watch", review)


if __name__ == "__main__":
    unittest.main()
