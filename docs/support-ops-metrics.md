# Support Ops Metrics

The incident triage side of this toolkit answers "what is wrong with this ticket?" This side answers the questions a support lead owns: is the team meeting its commitments, where is the volume coming from, what should Engineering fix, and what does each engineer need from their next 1:1?

## Flow

```text
data/support_tickets.csv   data/qa_reviews.csv
data/sla_policy.json       data/qa_rubric.json
            |                       |
            v                       v
   SLA outcomes per ticket    weighted QA scores
            |                       |
            +----------+------------+
                       v
        weekly trend, category and priority breakdowns,
        systemic issue detection, engineer coaching view
                       |
          +------------+-------------+
          v                          v
output/support-ops-metrics.json   output/weekly-support-review.md
          |
          v
dashboard/support-ops.html
```

`app/support_ops.py` uses only the Python standard library.

## Metric Definitions

| Metric | Definition | Why it matters |
| --- | --- | --- |
| First response SLA | Share of tickets whose first reply came within the priority's target | The customer's first signal that someone owns the problem |
| Resolution SLA | Share of tickets resolved within the priority's target | Contract commitment for enterprise customers |
| Median / p90 first response | 50th and 90th percentile minutes to first reply | The median shows the normal experience; p90 shows the tail that drives escalations |
| Median / p90 resolution | Same, in hours, for resolved tickets | Separates fast fixes from long-running investigations |
| Escalation rate | Tickets escalated to another team / all tickets | High rates point to missing runbooks, tooling, or access |
| Reopen rate | Resolved tickets that reopened / resolved tickets | A proxy for fix quality and closing without confirmation |
| CSAT | Average of 1-5 survey responses | Lagging indicator; read it next to the response count |
| Open tickets | Tickets with no resolution time at report time | Backlog for the next shift and weekend coverage |
| Urgent first response SLA | First response SLA on P1 and P2 tickets only, reported per customer tier | Overall attainment hides the tickets customers remember; see below |

### Pending is not a miss

An open ticket that is still inside its SLA window counts as **pending**, not breached, and is left out of attainment. Once the deadline passes without a response or resolution, it counts as a breach even though the ticket is still open. Without this rule, a report run on Monday morning would punish the team for tickets created ten minutes earlier.

### Report time

The report time (`as_of`) defaults to the last event in the data, so reruns on the same files give the same numbers. Pass `--as-of 2026-10-12T00:00:00Z` to pin it.

### Calendar time

Targets in `data/sla_policy.json` are measured in calendar time to keep the lab readable. A production policy usually adds business hours per customer tier and pauses the clock while waiting on the customer. Those belong in `sla_outcomes()` and would not change the rest of the pipeline.

## Systemic Issue Rules

A support lead's job is to make the next ticket unnecessary. The report flags categories whose pattern points to a product or process problem. Thresholds live in `data/sla_policy.json` under `systemic_issue_rules`.

| Signal | Rule | Default | Typical action |
| --- | --- | --- | --- |
| Volume spike | Last week's tickets / average of prior weeks | 1.5x or more, at least 5 tickets; 2x or more is critical | Problem record, check recent releases, ask Engineering for an owner and ETA |
| High escalation rate | Escalated / all tickets in the category | 25% or more | Find the top escalation reasons; close the gap with a runbook, tooling, log access, or training |
| High reopen rate | Reopened / resolved in the category | 12% or more | QA review the reopened tickets; confirm fixes with the customer before closing |

Categories with fewer than `min_tickets` tickets are skipped so one bad ticket does not look like a trend.

## SLA by Customer Tier

Every ticket carries a `customer_tier` (enterprise, growth, or standard). The report breaks SLA attainment, escalation rate, and CSAT down by tier, and adds **urgent first response SLA**: first response attainment on P1 and P2 tickets only.

Overall attainment can look healthy while the tickets that matter most are late. In the sample data, enterprise first response SLA is 89.3%, close to the 90% goal, but only 80% of enterprise P1 and P2 tickets got a first response on time. Enterprise also has the highest escalation rate and the lowest CSAT of the three tiers. That is the number to bring to Customer Success and to on-call planning.

## Engineer Coaching View

Each engineer gets ticket count, SLA attainment, escalation and reopen rates, CSAT, QA average, and a short coaching focus built from:

- their lowest QA rubric dimension, if it averages below 3 of 4
- any QA auto-fail, such as sensitive data in a ticket
- first response SLA below the team goal

The view is meant for 1:1s and development plans. Ticket counts depend on queue routing and ticket mix, so the dashboard does not rank engineers against each other.

## Sample Data Story

`scripts/generate_support_data.py` builds six weeks of fictional tickets with a fixed seed. A lead reviewing the dashboard should find:

- webhook delivery tickets jump in the last two weeks (a fictional release regression)
- risk score questions escalate to Engineering more than other categories
- the week of 2026-09-21 had thin on-call coverage, so P1 and P2 first responses slipped
- enterprise customers get the slowest urgent first responses, the most escalations, and the lowest CSAT
- QA reviews point to a different coaching need for each engineer, plus one auto-fail for a pasted API key

Regenerate with `python scripts/generate_support_data.py`.
