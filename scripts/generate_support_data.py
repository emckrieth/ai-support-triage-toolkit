"""Generate the fictional support ticket and QA review data used by the support ops lab.

The output is deterministic (fixed seed) so metrics, tests, and screenshots stay stable.
The data tells a story a support lead should be able to find:

- webhook delivery tickets spike in the last two weeks after a (fictional) platform release
- risk score questions escalate to Engineering more often than other categories
- one week has thin on-call coverage, so P1/P2 first responses slip
- QA reviews show different coaching needs per engineer
"""

from __future__ import annotations

import csv
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SEED = 20260831
START = datetime(2026, 8, 31, tzinfo=timezone.utc)  # Monday
WEEKS = 6
AS_OF = START + timedelta(weeks=WEEKS)

ENGINEERS = ["Avery", "Jordan", "Priya", "Mateo", "Sam"]
TIERS = [("enterprise", 0.35), ("growth", 0.40), ("standard", 0.25)]
CHANNELS = [("email", 0.45), ("slack_connect", 0.30), ("portal", 0.25)]
PRIORITIES = [("P1", 0.05), ("P2", 0.20), ("P3", 0.50), ("P4", 0.25)]

# category: (base weekly volume, escalation probability, escalation team)
CATEGORIES = {
    "api_authentication": (8, 0.10, "Engineering"),
    "webhook_delivery": (6, 0.20, "Engineering"),
    "risk_score_questions": (9, 0.45, "Engineering"),
    "sdk_integration": (7, 0.15, "Engineering"),
    "data_export_reporting": (5, 0.12, "Data Platform"),
    "dashboard_access": (6, 0.05, "Product"),
}

# Target first response minutes and resolution hours, used to shape realistic timings.
FIRST_RESPONSE_TARGET = {"P1": 15, "P2": 60, "P3": 240, "P4": 480}
RESOLUTION_TARGET = {"P1": 4, "P2": 24, "P3": 72, "P4": 120}

# Per engineer behavior: response speed multiplier, resolution multiplier, QA profile.
ENGINEER_PROFILE = {
    "Avery": {"speed": 0.8, "resolve": 0.9, "weak": None},
    "Jordan": {"speed": 1.0, "resolve": 1.1, "weak": "communication"},
    "Priya": {"speed": 0.9, "resolve": 0.8, "weak": None},
    "Mateo": {"speed": 1.3, "resolve": 1.2, "weak": "troubleshooting"},
    "Sam": {"speed": 1.0, "resolve": 1.0, "weak": "process"},
}

QA_DIMENSIONS = ["technical_accuracy", "troubleshooting", "communication", "process", "ownership"]


def weighted_choice(rng: random.Random, options: list[tuple[str, float]]) -> str:
    return rng.choices([name for name, _ in options], weights=[weight for _, weight in options])[0]


def iso(value: datetime | None) -> str:
    return value.strftime("%Y-%m-%dT%H:%M:%SZ") if value else ""


def weekly_volume(category: str, week: int, base: int) -> int:
    if category == "webhook_delivery" and week >= 4:
        return base * 3  # release regression in the last two weeks
    if category == "api_authentication" and week == 2:
        return base + 3  # key rotation reminder week
    return base


def build_tickets(rng: random.Random) -> list[dict[str, str]]:
    tickets: list[dict[str, str]] = []
    for week in range(WEEKS):
        week_start = START + timedelta(weeks=week)
        for category, (base, escalation_rate, escalation_team) in CATEGORIES.items():
            for _ in range(weekly_volume(category, week, base) + rng.randint(-1, 2)):
                created = week_start + timedelta(minutes=rng.randint(0, 7 * 24 * 60 - 1))
                if created >= AS_OF:
                    continue
                priority = weighted_choice(rng, PRIORITIES)
                if category == "webhook_delivery" and week >= 4 and rng.random() < 0.35:
                    priority = "P2"
                engineer = rng.choice(ENGINEERS)
                profile = ENGINEER_PROFILE[engineer]

                response_minutes = FIRST_RESPONSE_TARGET[priority] * rng.uniform(0.15, 1.05) * profile["speed"]
                if week == 3 and priority in {"P1", "P2"}:
                    response_minutes *= 2.2  # on-call gap week
                first_response = created + timedelta(minutes=response_minutes)

                escalated = rng.random() < escalation_rate
                resolve_hours = RESOLUTION_TARGET[priority] * rng.uniform(0.1, 1.0) * profile["resolve"]
                if escalated:
                    resolve_hours *= rng.uniform(1.2, 2.0)
                resolved: datetime | None = created + timedelta(hours=resolve_hours)
                if resolved >= AS_OF:
                    resolved = None
                if first_response >= AS_OF:
                    first_response = None

                reopened = resolved is not None and rng.random() < (0.16 if category == "webhook_delivery" else 0.05)
                csat = ""
                if resolved is not None and rng.random() < 0.45:
                    low = 2 if escalated or reopened else 3
                    csat = str(rng.randint(low, 5))

                tickets.append(
                    {
                        "created_at": iso(created),
                        "first_response_at": iso(first_response),
                        "resolved_at": iso(resolved),
                        "priority": priority,
                        "customer_tier": weighted_choice(rng, TIERS),
                        "category": category,
                        "channel": weighted_choice(rng, CHANNELS),
                        "assignee": engineer,
                        "escalated_to": escalation_team if escalated else "",
                        "reopened": "1" if reopened else "0",
                        "csat": csat,
                    }
                )
    tickets.sort(key=lambda item: item["created_at"])
    for index, ticket in enumerate(tickets, start=1):
        ticket["ticket_id"] = f"SUP-{4100 + index}"
    return tickets


def build_qa_reviews(rng: random.Random, tickets: list[dict[str, str]]) -> list[dict[str, str]]:
    reviews = []
    resolved = [ticket for ticket in tickets if ticket["resolved_at"]]
    for engineer in ENGINEERS:
        sample = rng.sample([ticket for ticket in resolved if ticket["assignee"] == engineer], 6)
        for ticket in sorted(sample, key=lambda item: item["ticket_id"]):
            weak = ENGINEER_PROFILE[engineer]["weak"]
            scores = {}
            for dimension in QA_DIMENSIONS:
                if dimension == weak:
                    scores[dimension] = rng.choice([2, 2, 3])
                else:
                    scores[dimension] = rng.choice([3, 4, 4])
            auto_fail = ""
            if engineer == "Sam" and ticket is sample[0]:
                auto_fail = "customer API key pasted in ticket reply"
            reviews.append(
                {
                    "ticket_id": ticket["ticket_id"],
                    "engineer": engineer,
                    "reviewer": "Support Lead",
                    **{dimension: str(score) for dimension, score in scores.items()},
                    "auto_fail_reason": auto_fail,
                }
            )
    return reviews


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    rng = random.Random(SEED)
    tickets = build_tickets(rng)
    reviews = build_qa_reviews(rng, tickets)
    write_csv(
        ROOT / "data" / "support_tickets.csv",
        tickets,
        [
            "ticket_id",
            "created_at",
            "first_response_at",
            "resolved_at",
            "priority",
            "customer_tier",
            "category",
            "channel",
            "assignee",
            "escalated_to",
            "reopened",
            "csat",
        ],
    )
    write_csv(
        ROOT / "data" / "qa_reviews.csv",
        reviews,
        ["ticket_id", "engineer", "reviewer", *QA_DIMENSIONS, "auto_fail_reason"],
    )
    print(f"Wrote {len(tickets)} tickets and {len(reviews)} QA reviews")


if __name__ == "__main__":
    main()
