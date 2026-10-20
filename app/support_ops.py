from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any

from app.triage import load_json, write_json


def parse_time(value: str) -> datetime | None:
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def load_tickets(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    tickets = []
    for row in rows:
        tickets.append(
            {
                **row,
                "created_at": parse_time(row["created_at"]),
                "first_response_at": parse_time(row["first_response_at"]),
                "resolved_at": parse_time(row["resolved_at"]),
                "reopened": row.get("reopened") == "1",
                "csat": int(row["csat"]) if row.get("csat") else None,
            }
        )
    return tickets


def load_qa_reviews(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def percentile(values: list[float], pct: float) -> float | None:
    """Linear interpolation percentile, the same method as most BI tools."""
    if not values:
        return None
    ordered = sorted(values)
    rank = (len(ordered) - 1) * pct / 100
    low = math.floor(rank)
    high = math.ceil(rank)
    if low == high:
        return ordered[low]
    return ordered[low] + (ordered[high] - ordered[low]) * (rank - low)


def rate(part: int, whole: int) -> float | None:
    return round(part / whole * 100, 1) if whole else None


def round_or_none(value: float | None, digits: int = 1) -> float | None:
    return round(value, digits) if value is not None else None


def sla_outcomes(ticket: dict[str, Any], policy: dict[str, Any], as_of: datetime) -> dict[str, str]:
    """Return met / breached / pending for first response and resolution.

    An open ticket is only counted once its target has passed: a ticket still inside
    its window is pending, not a miss, so the attainment rate is not dragged down by
    work that is on track.
    """
    target = policy["priorities"][ticket["priority"]]
    created = ticket["created_at"]
    outcomes = {}
    checks = [
        ("first_response", ticket["first_response_at"], timedelta(minutes=target["first_response_minutes"])),
        ("resolution", ticket["resolved_at"], timedelta(hours=target["resolution_hours"])),
    ]
    for name, completed, allowed in checks:
        deadline = created + allowed
        if completed is not None:
            outcomes[name] = "met" if completed <= deadline else "breached"
        else:
            outcomes[name] = "breached" if as_of > deadline else "pending"
    return outcomes


def attainment(outcomes: list[str]) -> float | None:
    decided = [item for item in outcomes if item != "pending"]
    return rate(sum(1 for item in decided if item == "met"), len(decided))


def core_metrics(tickets: list[dict[str, Any]], policy: dict[str, Any], as_of: datetime) -> dict[str, Any]:
    outcomes = [sla_outcomes(ticket, policy, as_of) for ticket in tickets]
    first_response_minutes = [
        (ticket["first_response_at"] - ticket["created_at"]).total_seconds() / 60
        for ticket in tickets
        if ticket["first_response_at"]
    ]
    resolution_hours = [
        (ticket["resolved_at"] - ticket["created_at"]).total_seconds() / 3600
        for ticket in tickets
        if ticket["resolved_at"]
    ]
    csat = [ticket["csat"] for ticket in tickets if ticket["csat"] is not None]
    resolved = [ticket for ticket in tickets if ticket["resolved_at"]]
    return {
        "tickets": len(tickets),
        "first_response_sla_percent": attainment([item["first_response"] for item in outcomes]),
        "resolution_sla_percent": attainment([item["resolution"] for item in outcomes]),
        "median_first_response_minutes": round_or_none(percentile(first_response_minutes, 50)),
        "p90_first_response_minutes": round_or_none(percentile(first_response_minutes, 90)),
        "median_resolution_hours": round_or_none(percentile(resolution_hours, 50)),
        "p90_resolution_hours": round_or_none(percentile(resolution_hours, 90)),
        "escalation_rate_percent": rate(sum(1 for ticket in tickets if ticket["escalated_to"]), len(tickets)),
        "reopen_rate_percent": rate(sum(1 for ticket in resolved if ticket["reopened"]), len(resolved)),
        "csat_average": round(mean(csat), 2) if csat else None,
        "csat_responses": len(csat),
        "open_tickets": sum(1 for ticket in tickets if ticket["resolved_at"] is None),
        "sla_breaches": sum(1 for item in outcomes for value in item.values() if value == "breached"),
    }


def latest_activity(tickets: list[dict[str, Any]]) -> datetime:
    """Default report time: the last recorded event, so reruns on the same data give the same numbers."""
    stamps = [
        stamp
        for ticket in tickets
        for stamp in (ticket["created_at"], ticket["first_response_at"], ticket["resolved_at"])
        if stamp is not None
    ]
    return max(stamps)


def week_start(value: datetime) -> str:
    monday = value - timedelta(days=value.weekday())
    return monday.strftime("%Y-%m-%d")


def group_by(tickets: list[dict[str, Any]], key) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for ticket in tickets:
        groups[key(ticket)].append(ticket)
    return dict(sorted(groups.items()))


def weekly_trend(tickets: list[dict[str, Any]], policy: dict[str, Any], as_of: datetime) -> list[dict[str, Any]]:
    weeks = group_by(tickets, lambda ticket: week_start(ticket["created_at"]))
    return [{"week": week, **core_metrics(items, policy, as_of)} for week, items in weeks.items()]


def category_breakdown(tickets: list[dict[str, Any]], policy: dict[str, Any], as_of: datetime) -> list[dict[str, Any]]:
    all_weeks = sorted({week_start(ticket["created_at"]) for ticket in tickets})
    latest_week = all_weeks[-1]
    prior_week_count = len(all_weeks) - 1
    rows = []
    for category, items in group_by(tickets, lambda ticket: ticket["category"]).items():
        weekly_counts = defaultdict(int)
        for ticket in items:
            weekly_counts[week_start(ticket["created_at"])] += 1
        prior_total = sum(count for week, count in weekly_counts.items() if week != latest_week)
        baseline = prior_total / prior_week_count if prior_week_count else 0
        metrics = core_metrics(items, policy, as_of)
        rows.append(
            {
                "category": category,
                "latest_week_tickets": weekly_counts.get(latest_week, 0),
                "prior_weekly_average": round(baseline, 1),
                "escalation_targets": sorted({ticket["escalated_to"] for ticket in items if ticket["escalated_to"]}),
                **metrics,
            }
        )
    return sorted(rows, key=lambda row: row["tickets"], reverse=True)


def detect_systemic_issues(categories: list[dict[str, Any]], rules: dict[str, Any]) -> list[dict[str, Any]]:
    """Flag categories whose pattern suggests a product or process problem, not a one-off ticket."""
    issues = []
    for row in categories:
        if row["tickets"] < rules["min_tickets"]:
            continue
        baseline = row["prior_weekly_average"]
        latest = row["latest_week_tickets"]
        if latest >= rules["min_tickets"] and baseline and latest / baseline >= rules["volume_spike_ratio"]:
            issues.append(
                {
                    "category": row["category"],
                    "signal": "volume spike",
                    "severity": "critical" if latest / baseline >= 2 else "serious",
                    "evidence": f"{latest} tickets last week vs {baseline:g} weekly average before it ({latest / baseline:.1f}x).",
                    "action": "Open a problem record, check recent releases and status page history, and ask Engineering for a fix owner and ETA.",
                }
            )
        escalation = row["escalation_rate_percent"] or 0
        if escalation >= rules["escalation_rate_percent"]:
            issues.append(
                {
                    "category": row["category"],
                    "signal": "high escalation rate",
                    "severity": "serious",
                    "evidence": f"{escalation:g}% of tickets escalated (rule: {rules['escalation_rate_percent']}%).",
                    "action": "Find the top escalation reasons, then close the gap with a runbook, a tool or log access for support, or training.",
                }
            )
        reopen = row["reopen_rate_percent"] or 0
        if reopen >= rules["reopen_rate_percent"]:
            issues.append(
                {
                    "category": row["category"],
                    "signal": "high reopen rate",
                    "severity": "warning",
                    "evidence": f"{reopen:g}% of resolved tickets reopened (rule: {rules['reopen_rate_percent']}%).",
                    "action": "QA review reopened tickets; check whether fixes are confirmed with the customer before closing.",
                }
            )
    order = {"critical": 0, "serious": 1, "warning": 2}
    return sorted(issues, key=lambda issue: (order[issue["severity"]], issue["category"]))


def score_review(review: dict[str, str], rubric: dict[str, Any]) -> dict[str, Any]:
    top = rubric["scale"]["max"]
    dimension_scores = {item["key"]: int(review[item["key"]]) for item in rubric["dimensions"]}
    weighted = sum(item["weight"] * dimension_scores[item["key"]] / top for item in rubric["dimensions"]) * 100
    auto_fail = review.get("auto_fail_reason", "").strip()
    score = 0.0 if auto_fail else round(weighted, 1)
    return {
        "ticket_id": review["ticket_id"],
        "engineer": review["engineer"],
        "score": score,
        "passed": score >= rubric["pass_percent"],
        "auto_fail_reason": auto_fail,
        "dimension_scores": dimension_scores,
    }


def qa_summary(reviews: list[dict[str, str]], rubric: dict[str, Any]) -> dict[str, Any]:
    scored = [score_review(review, rubric) for review in reviews]
    dimensions = []
    for item in rubric["dimensions"]:
        values = [review["dimension_scores"][item["key"]] for review in scored]
        dimensions.append(
            {
                "key": item["key"],
                "name": item["name"],
                "weight": item["weight"],
                "average": round(mean(values), 2) if values else None,
            }
        )
    return {
        "reviews": len(scored),
        "average_score": round(mean(review["score"] for review in scored), 1) if scored else None,
        "pass_rate_percent": rate(sum(1 for review in scored if review["passed"]), len(scored)),
        "auto_fails": [review for review in scored if review["auto_fail_reason"]],
        "dimensions": dimensions,
        "scored_reviews": scored,
    }


def engineer_scorecards(
    tickets: list[dict[str, Any]],
    qa: dict[str, Any],
    rubric: dict[str, Any],
    policy: dict[str, Any],
    as_of: datetime,
) -> list[dict[str, Any]]:
    """Coaching view per engineer. Built for 1:1s, not for stack ranking."""
    coaching = {item["key"]: item for item in rubric["dimensions"]}
    reviews_by_engineer = defaultdict(list)
    for review in qa["scored_reviews"]:
        reviews_by_engineer[review["engineer"]].append(review)

    cards = []
    for engineer, items in group_by(tickets, lambda ticket: ticket["assignee"]).items():
        metrics = core_metrics(items, policy, as_of)
        reviews = reviews_by_engineer.get(engineer, [])
        dimension_averages = {
            key: mean(review["dimension_scores"][key] for review in reviews) for key in coaching
        } if reviews else {}
        weakest = min(dimension_averages, key=dimension_averages.get) if dimension_averages else None
        focus = []
        if weakest and dimension_averages[weakest] < 3:
            focus.append(f"{coaching[weakest]['name']}: {coaching[weakest]['coaching']}")
        if any(review["auto_fail_reason"] for review in reviews):
            focus.append("Data handling: review the sensitive data rules together before the next shift.")
        goal = policy["attainment_goal_percent"]
        if (metrics["first_response_sla_percent"] or 0) < goal:
            focus.append("First response: check queue views and notification settings; agree on a triage cadence.")
        cards.append(
            {
                "engineer": engineer,
                "tickets": metrics["tickets"],
                "first_response_sla_percent": metrics["first_response_sla_percent"],
                "resolution_sla_percent": metrics["resolution_sla_percent"],
                "escalation_rate_percent": metrics["escalation_rate_percent"],
                "reopen_rate_percent": metrics["reopen_rate_percent"],
                "csat_average": metrics["csat_average"],
                "qa_average": round(mean(review["score"] for review in reviews), 1) if reviews else None,
                "qa_reviews": len(reviews),
                "weakest_qa_dimension": coaching[weakest]["name"] if weakest else None,
                "coaching_focus": focus or ["Keep doing what works; consider mentoring or writing KB articles."],
            }
        )
    return cards


def priority_breakdown(tickets: list[dict[str, Any]], policy: dict[str, Any], as_of: datetime) -> list[dict[str, Any]]:
    rows = []
    for priority, items in group_by(tickets, lambda ticket: ticket["priority"]).items():
        target = policy["priorities"][priority]
        rows.append(
            {
                "priority": priority,
                "first_response_target_minutes": target["first_response_minutes"],
                "resolution_target_hours": target["resolution_hours"],
                **core_metrics(items, policy, as_of),
            }
        )
    return rows


TIER_ORDER = ["enterprise", "growth", "standard"]
URGENT_PRIORITIES = {"P1", "P2"}


def tier_breakdown(tickets: list[dict[str, Any]], policy: dict[str, Any], as_of: datetime) -> list[dict[str, Any]]:
    """SLA by customer tier. Urgent first response is reported separately because averages hide it."""
    groups = group_by(tickets, lambda ticket: ticket["customer_tier"])
    rows = []
    for tier in sorted(groups, key=lambda name: TIER_ORDER.index(name) if name in TIER_ORDER else len(TIER_ORDER)):
        items = groups[tier]
        urgent = [ticket for ticket in items if ticket["priority"] in URGENT_PRIORITIES]
        rows.append(
            {
                "tier": tier,
                "urgent_tickets": len(urgent),
                "urgent_first_response_sla_percent": core_metrics(urgent, policy, as_of)["first_response_sla_percent"] if urgent else None,
                **core_metrics(items, policy, as_of),
            }
        )
    return rows


def build_report(
    tickets: list[dict[str, Any]],
    reviews: list[dict[str, str]],
    policy: dict[str, Any],
    rubric: dict[str, Any],
    as_of: datetime | None = None,
) -> dict[str, Any]:
    as_of = as_of or latest_activity(tickets)
    weeks = weekly_trend(tickets, policy, as_of)
    categories = category_breakdown(tickets, policy, as_of)
    qa = qa_summary(reviews, rubric)
    return {
        "as_of": as_of.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "period": {"start": weeks[0]["week"], "end_week": weeks[-1]["week"], "weeks": len(weeks)},
        "attainment_goal_percent": policy["attainment_goal_percent"],
        "overall": core_metrics(tickets, policy, as_of),
        "latest_week": weeks[-1],
        "previous_week": weeks[-2] if len(weeks) > 1 else None,
        "weekly": weeks,
        "priorities": priority_breakdown(tickets, policy, as_of),
        "tiers": tier_breakdown(tickets, policy, as_of),
        "categories": categories,
        "systemic_issues": detect_systemic_issues(categories, policy["systemic_issue_rules"]),
        "engineers": engineer_scorecards(tickets, qa, rubric, policy, as_of),
        "qa": {key: value for key, value in qa.items() if key != "scored_reviews"},
    }


def fmt(value: Any, suffix: str = "") -> str:
    if value is None:
        return "n/a"
    return f"{value:g}{suffix}" if isinstance(value, (int, float)) else f"{value}{suffix}"


def delta(current: float | None, previous: float | None, suffix: str = "") -> str:
    if current is None or previous is None:
        return ""
    change = round(current - previous, 1)
    sign = "+" if change > 0 else ""
    return f" ({sign}{change:g}{suffix} vs prior week)"


def build_weekly_review(report: dict[str, Any]) -> str:
    latest = report["latest_week"]
    previous = report["previous_week"] or {}
    goal = report["attainment_goal_percent"]
    lines = [
        f"# Weekly Support Review - week of {latest['week']}",
        "",
        "Generated from ticket and QA data. Numbers are calendar time; open tickets inside their SLA window count as pending, not missed.",
        "",
        "## Headline",
        "",
        f"- Tickets created: {latest['tickets']}{delta(latest['tickets'], previous.get('tickets'))}",
        f"- First response SLA: {fmt(latest['first_response_sla_percent'], '%')} (goal {goal}%){delta(latest['first_response_sla_percent'], previous.get('first_response_sla_percent'), ' pts')}",
        f"- Resolution SLA: {fmt(latest['resolution_sla_percent'], '%')} (goal {goal}%){delta(latest['resolution_sla_percent'], previous.get('resolution_sla_percent'), ' pts')}",
        f"- Median first response: {fmt(latest['median_first_response_minutes'], ' min')}, p90 {fmt(latest['p90_first_response_minutes'], ' min')}",
        f"- Escalation rate: {fmt(latest['escalation_rate_percent'], '%')}{delta(latest['escalation_rate_percent'], previous.get('escalation_rate_percent'), ' pts')}",
        f"- CSAT: {fmt(latest['csat_average'])} from {latest['csat_responses']} responses",
        f"- Open tickets at report time: {report['overall']['open_tickets']}",
        "",
        "## Systemic issues to raise with Engineering and Product",
        "",
    ]
    if report["systemic_issues"]:
        for issue in report["systemic_issues"]:
            lines.append(f"- **{issue['category']}** - {issue['signal']} ({issue['severity']}). {issue['evidence']} Next step: {issue['action']}")
    else:
        lines.append("- None crossed the thresholds this period.")

    lines.extend(["", "## SLA by priority (whole period)", "", "| Priority | Tickets | First response SLA | Resolution SLA | Median first response |", "| --- | --- | --- | --- | --- |"])
    for row in report["priorities"]:
        lines.append(
            f"| {row['priority']} | {row['tickets']} | {fmt(row['first_response_sla_percent'], '%')} | {fmt(row['resolution_sla_percent'], '%')} | {fmt(row['median_first_response_minutes'], ' min')} |"
        )

    lines.extend(
        [
            "",
            "## SLA by customer tier (whole period)",
            "",
            "| Tier | Tickets | First response SLA | Resolution SLA | P1/P2 first response SLA | Escalation rate | CSAT |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in report["tiers"]:
        lines.append(
            f"| {row['tier']} | {row['tickets']} | {fmt(row['first_response_sla_percent'], '%')} | {fmt(row['resolution_sla_percent'], '%')} | "
            f"{fmt(row['urgent_first_response_sla_percent'], '%')} ({row['urgent_tickets']} tickets) | {fmt(row['escalation_rate_percent'], '%')} | {fmt(row['csat_average'])} |"
        )

    weeks = report["weekly"]
    worst = min(weeks, key=lambda week: week["first_response_sla_percent"] or 100)
    if (worst["first_response_sla_percent"] or 100) < goal:
        lines.extend(
            [
                "",
                "## Trend to watch",
                "",
                f"- First response SLA dipped to {fmt(worst['first_response_sla_percent'], '%')} in the week of {worst['week']}. Check on-call coverage and queue routing for that week before it repeats.",
            ]
        )

    qa = report["qa"]
    lines.extend(
        [
            "",
            "## Quality review",
            "",
            f"- {qa['reviews']} tickets reviewed, average score {fmt(qa['average_score'])}, pass rate {fmt(qa['pass_rate_percent'], '%')}",
        ]
    )
    weakest = min(qa["dimensions"], key=lambda item: item["average"])
    lines.append(f"- Lowest team dimension: {weakest['name']} ({weakest['average']:g} of 4)")
    for review in qa["auto_fails"]:
        lines.append(f"- Auto-fail on {review['ticket_id']}: {review['auto_fail_reason']}. Handle in a 1:1 and check for a tooling fix.")

    lines.extend(["", "## Coaching focus for 1:1s", ""])
    for card in report["engineers"]:
        lines.append(f"- **{card['engineer']}** ({card['tickets']} tickets, QA {fmt(card['qa_average'])}): {' '.join(card['coaching_focus'])}")

    lines.extend(
        [
            "",
            "## Asks",
            "",
            "- Engineering: owner and ETA for each critical systemic issue above.",
            "- Product: decide whether repeat how-to questions need product or docs changes.",
            "- Support team: one KB article per systemic issue so the next ticket is faster.",
        ]
    )
    return "\n".join(lines) + "\n"


def run(
    tickets_path: Path,
    qa_path: Path,
    policy_path: Path,
    rubric_path: Path,
    output_path: Path,
    review_path: Path | None = None,
    as_of: datetime | None = None,
) -> dict[str, Any]:
    report = build_report(
        load_tickets(tickets_path),
        load_qa_reviews(qa_path),
        load_json(policy_path),
        load_json(rubric_path),
        as_of,
    )
    write_json(output_path, report)
    if review_path:
        review_path.parent.mkdir(parents=True, exist_ok=True)
        review_path.write_text(build_weekly_review(report), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Build support team metrics, SLA attainment, QA scores, and a weekly review.")
    parser.add_argument("--tickets", default="data/support_tickets.csv", type=Path)
    parser.add_argument("--qa", default="data/qa_reviews.csv", type=Path)
    parser.add_argument("--policy", default="data/sla_policy.json", type=Path)
    parser.add_argument("--rubric", default="data/qa_rubric.json", type=Path)
    parser.add_argument("--output", default="output/support-ops-metrics.json", type=Path)
    parser.add_argument("--review", default="output/weekly-support-review.md", type=Path)
    parser.add_argument("--as-of", type=parse_time, help="Report time in UTC, e.g. 2026-10-12T00:00:00Z. Defaults to the last event in the data.")
    args = parser.parse_args()
    report = run(args.tickets, args.qa, args.policy, args.rubric, args.output, args.review, args.as_of)
    overall = report["overall"]
    print(f"Processed {overall['tickets']} tickets across {report['period']['weeks']} weeks")
    print(f"First response SLA {fmt(overall['first_response_sla_percent'], '%')}, resolution SLA {fmt(overall['resolution_sla_percent'], '%')}")
    for issue in report["systemic_issues"]:
        print(f"Systemic issue: {issue['category']} - {issue['signal']} ({issue['severity']})")


if __name__ == "__main__":
    main()
