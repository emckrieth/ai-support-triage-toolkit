import json
import shutil
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.support_ops import (
    build_report,
    build_weekly_review,
    detect_systemic_issues,
    percentile,
    run,
    score_review,
    sla_outcomes,
    tier_breakdown,
)
from app.triage import load_json


ROOT = Path(__file__).resolve().parents[1]
POLICY = load_json(ROOT / "data" / "sla_policy.json")
RUBRIC = load_json(ROOT / "data" / "qa_rubric.json")
START = datetime(2026, 10, 5, 9, 0, tzinfo=timezone.utc)


def ticket(priority="P2", response_minutes=30, resolve_hours=10, **overrides):
    created = overrides.pop("created_at", START)
    return {
        "ticket_id": overrides.pop("ticket_id", "SUP-1"),
        "created_at": created,
        "first_response_at": created + timedelta(minutes=response_minutes) if response_minutes is not None else None,
        "resolved_at": created + timedelta(hours=resolve_hours) if resolve_hours is not None else None,
        "priority": priority,
        "category": overrides.pop("category", "webhook_delivery"),
        "customer_tier": overrides.pop("customer_tier", "growth"),
        "assignee": overrides.pop("assignee", "Avery"),
        "escalated_to": overrides.pop("escalated_to", ""),
        "reopened": overrides.pop("reopened", False),
        "csat": overrides.pop("csat", None),
        **overrides,
    }


class SlaTests(unittest.TestCase):
    def test_met_and_breached(self):
        on_time = sla_outcomes(ticket("P2", 59, 23), POLICY, START + timedelta(days=2))
        late = sla_outcomes(ticket("P2", 61, 25), POLICY, START + timedelta(days=2))

        self.assertEqual(on_time, {"first_response": "met", "resolution": "met"})
        self.assertEqual(late, {"first_response": "breached", "resolution": "breached"})

    def test_open_ticket_is_pending_until_deadline_passes(self):
        open_ticket = ticket("P1", None, None)

        inside = sla_outcomes(open_ticket, POLICY, START + timedelta(minutes=10))
        after = sla_outcomes(open_ticket, POLICY, START + timedelta(hours=5))

        self.assertEqual(inside, {"first_response": "pending", "resolution": "pending"})
        self.assertEqual(after, {"first_response": "breached", "resolution": "breached"})

    def test_percentile_interpolates(self):
        self.assertEqual(percentile([10, 20, 30, 40], 50), 25)
        self.assertEqual(percentile([5], 90), 5)
        self.assertIsNone(percentile([], 50))


class SystemicIssueTests(unittest.TestCase):
    def test_volume_spike_and_escalation_rules(self):
        rules = POLICY["systemic_issue_rules"]
        categories = [
            {"category": "webhook_delivery", "tickets": 40, "latest_week_tickets": 18, "prior_weekly_average": 6.0,
             "escalation_rate_percent": 10.0, "reopen_rate_percent": 2.0},
            {"category": "risk_score_questions", "tickets": 30, "latest_week_tickets": 5, "prior_weekly_average": 5.0,
             "escalation_rate_percent": 40.0, "reopen_rate_percent": 0.0},
            {"category": "dashboard_access", "tickets": 20, "latest_week_tickets": 4, "prior_weekly_average": 4.0,
             "escalation_rate_percent": 5.0, "reopen_rate_percent": 0.0},
        ]

        issues = detect_systemic_issues(categories, rules)
        found = {(issue["category"], issue["signal"]) for issue in issues}

        self.assertIn(("webhook_delivery", "volume spike"), found)
        self.assertIn(("risk_score_questions", "high escalation rate"), found)
        self.assertFalse(any(issue["category"] == "dashboard_access" for issue in issues))
        self.assertEqual(issues[0]["severity"], "critical")


class TierTests(unittest.TestCase):
    def test_tiers_are_ordered_and_urgent_sla_counts_only_p1_p2(self):
        as_of = START + timedelta(days=3)
        tickets = [
            ticket("P1", 30, ticket_id="SUP-1", customer_tier="enterprise"),  # 30 min > 15 min target: breached
            ticket("P3", 30, ticket_id="SUP-2", customer_tier="enterprise"),
            ticket("P2", 30, ticket_id="SUP-3", customer_tier="standard"),
            ticket("P4", 30, ticket_id="SUP-4", customer_tier="growth"),
        ]

        rows = tier_breakdown(tickets, POLICY, as_of)

        self.assertEqual([row["tier"] for row in rows], ["enterprise", "growth", "standard"])
        enterprise = rows[0]
        self.assertEqual(enterprise["tickets"], 2)
        self.assertEqual(enterprise["urgent_tickets"], 1)
        self.assertEqual(enterprise["urgent_first_response_sla_percent"], 0)
        self.assertEqual(enterprise["first_response_sla_percent"], 50)
        self.assertIsNone(rows[1]["urgent_first_response_sla_percent"])
        self.assertEqual(rows[2]["urgent_first_response_sla_percent"], 100)


class QaTests(unittest.TestCase):
    def test_weighted_score_and_auto_fail(self):
        perfect = {"ticket_id": "SUP-1", "engineer": "Avery", "technical_accuracy": "4", "troubleshooting": "4",
                   "communication": "4", "process": "4", "ownership": "4", "auto_fail_reason": ""}
        weak = {**perfect, "communication": "2"}
        failed = {**perfect, "auto_fail_reason": "API key pasted in reply"}

        self.assertEqual(score_review(perfect, RUBRIC)["score"], 100)
        self.assertEqual(score_review(weak, RUBRIC)["score"], 90)
        self.assertEqual(score_review(failed, RUBRIC)["score"], 0)
        self.assertFalse(score_review(failed, RUBRIC)["passed"])

    def test_rubric_weights_sum_to_one(self):
        self.assertAlmostEqual(sum(item["weight"] for item in RUBRIC["dimensions"]), 1.0)


class ReportTests(unittest.TestCase):
    def test_report_from_small_dataset(self):
        tickets = [
            ticket(ticket_id="SUP-1", escalated_to="Engineering", csat=4),
            ticket(ticket_id="SUP-2", response_minutes=90, assignee="Jordan", reopened=True, csat=2),
            ticket(ticket_id="SUP-3", created_at=START - timedelta(days=7), category="api_authentication"),
        ]
        reviews = [{"ticket_id": "SUP-1", "engineer": "Avery", "technical_accuracy": "4", "troubleshooting": "3",
                    "communication": "4", "process": "4", "ownership": "4", "auto_fail_reason": ""}]

        report = build_report(tickets, reviews, POLICY, RUBRIC, as_of=START + timedelta(days=3))

        self.assertEqual(report["overall"]["tickets"], 3)
        self.assertEqual(report["overall"]["first_response_sla_percent"], 66.7)
        self.assertEqual(report["overall"]["escalation_rate_percent"], 33.3)
        self.assertEqual(report["overall"]["csat_average"], 3)
        self.assertEqual([week["week"] for week in report["weekly"]], ["2026-09-28", "2026-10-05"])
        self.assertEqual(report["latest_week"]["tickets"], 2)
        self.assertIn("Weekly Support Review", build_weekly_review(report))

    def test_sample_data_end_to_end(self):
        output_dir = ROOT / ".tmp-test"
        shutil.rmtree(output_dir, ignore_errors=True)
        output_dir.mkdir()
        try:
            report = run(
                ROOT / "data" / "support_tickets.csv",
                ROOT / "data" / "qa_reviews.csv",
                ROOT / "data" / "sla_policy.json",
                ROOT / "data" / "qa_rubric.json",
                output_dir / "metrics.json",
                output_dir / "review.md",
            )
            saved = json.loads((output_dir / "metrics.json").read_text(encoding="utf-8"))
            review = (output_dir / "review.md").read_text(encoding="utf-8")
        finally:
            shutil.rmtree(output_dir, ignore_errors=True)

        self.assertEqual(saved["overall"]["tickets"], report["overall"]["tickets"])
        self.assertEqual(report["period"]["weeks"], 6)
        signals = {(issue["category"], issue["signal"]) for issue in report["systemic_issues"]}
        self.assertIn(("webhook_delivery", "volume spike"), signals)
        self.assertIn(("risk_score_questions", "high escalation rate"), signals)
        self.assertEqual(len(report["qa"]["auto_fails"]), 1)
        self.assertIn("Coaching focus", review)
        self.assertIn("SLA by customer tier", review)
        self.assertEqual([row["tier"] for row in report["tiers"]], ["enterprise", "growth", "standard"])
        self.assertEqual(sum(row["tickets"] for row in report["tiers"]), report["overall"]["tickets"])


if __name__ == "__main__":
    unittest.main()
