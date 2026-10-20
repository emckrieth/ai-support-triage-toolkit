# Weekly Support Review - week of 2026-10-05

Generated from ticket and QA data. Numbers are calendar time; open tickets inside their SLA window count as pending, not missed.

## Headline

- Tickets created: 54 (+1 vs prior week)
- First response SLA: 94.3% (goal 90%) (-3.8 pts vs prior week)
- Resolution SLA: 95.5% (goal 90%) (+1.2 pts vs prior week)
- Median first response: 95.2 min, p90 269.5 min
- Escalation rate: 18.5% (+11 pts vs prior week)
- CSAT: 3.85 from 20 responses
- Open tickets at report time: 10

## Systemic issues to raise with Engineering and Product

- **webhook_delivery** - volume spike (critical). 20 tickets last week vs 7.6 weekly average before it (2.6x). Next step: Open a problem record, check recent releases and status page history, and ask Engineering for a fix owner and ETA.
- **risk_score_questions** - high escalation rate (serious). 28.1% of tickets escalated (rule: 25%). Next step: Find the top escalation reasons, then close the gap with a runbook, a tool or log access for support, or training.
- **sdk_integration** - high reopen rate (warning). 16.7% of resolved tickets reopened (rule: 12%). Next step: QA review reopened tickets; check whether fixes are confirmed with the customer before closing.
- **webhook_delivery** - high reopen rate (warning). 16.1% of resolved tickets reopened (rule: 12%). Next step: QA review reopened tickets; check whether fixes are confirmed with the customer before closing.

## SLA by priority (whole period)

| Priority | Tickets | First response SLA | Resolution SLA | Median first response |
| --- | --- | --- | --- | --- |
| P1 | 22 | 72.7% | 90.9% | 10.7 min |
| P2 | 73 | 80.8% | 87.5% | 37.1 min |
| P3 | 123 | 91.8% | 94% | 136.5 min |
| P4 | 69 | 94.2% | 92.5% | 282.6 min |

## SLA by customer tier (whole period)

| Tier | Tickets | First response SLA | Resolution SLA | P1/P2 first response SLA | Escalation rate | CSAT |
| --- | --- | --- | --- | --- | --- | --- |
| enterprise | 103 | 89.3% | 93.9% | 80% (40 tickets) | 16.5% | 3.73 |
| growth | 110 | 88.1% | 87.7% | 71% (31 tickets) | 12.7% | 4.06 |
| standard | 74 | 86.5% | 94.5% | 87.5% (24 tickets) | 10.8% | 4.12 |

## Trend to watch

- First response SLA dipped to 70.5% in the week of 2026-09-21. Check on-call coverage and queue routing for that week before it repeats.

## Quality review

- 30 tickets reviewed, average score 82.8, pass rate 76.7%
- Lowest team dimension: Communication (3.27 of 4)
- Auto-fail on SUP-4194: customer API key pasted in ticket reply. Handle in a 1:1 and check for a tooling fix.

## Coaching focus for 1:1s

- **Avery** (62 tickets, QA 87.1): Keep doing what works; consider mentoring or writing KB articles.
- **Jordan** (56 tickets, QA 79.4): Communication: Review two strong replies together and practice the 'what we know / what we are doing / next update' format.
- **Mateo** (62 tickets, QA 82.5): Troubleshooting: Use the evidence checklist in each runbook and ask for request IDs and timestamps in the first reply. First response: check queue views and notification settings; agree on a triage cadence.
- **Priya** (58 tickets, QA 94.4): Keep doing what works; consider mentoring or writing KB articles.
- **Sam** (49 tickets, QA 70.8): Process and documentation: Walk through the escalation template and the data handling rules; spot check tickets for two weeks. Data handling: review the sensitive data rules together before the next shift.

## Asks

- Engineering: owner and ETA for each critical systemic issue above.
- Product: decide whether repeat how-to questions need product or docs changes.
- Support team: one KB article per systemic issue so the next ticket is faster.
