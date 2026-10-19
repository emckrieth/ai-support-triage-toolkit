# Ticket Quality Review Framework

Metrics show speed. Quality review shows whether the answers were right, clear, and safe. The rubric lives in `data/qa_rubric.json` so a team can change weights without changing code.

## Cadence

- Review about 6 resolved tickets per engineer per month, chosen at random plus any ticket with low CSAT, a reopen, or an escalation.
- Reviewers rotate: the support lead plus one senior engineer, so the bar stays shared.
- Calibrate monthly: two reviewers score the same three tickets and discuss differences above one point.

## Rubric

Each dimension is scored 1-4. The ticket score is the weighted average scaled to 100. The pass mark is 80.

| Dimension | Weight | 4 - Excellent | 2 - Needs work |
| --- | --- | --- | --- |
| Technical accuracy | 30% | Correct for the customer's API version and setup; verified before sending | Partly correct or generic; customer had to come back |
| Troubleshooting | 25% | Asked for request IDs and timestamps up front; isolated the cause with evidence | Guessed, or asked for information one piece at a time |
| Communication | 20% | Clear summary, next steps, and next update time; no unexplained jargon | Hard to follow, no expectation set |
| Process and documentation | 15% | Correct priority and category, internal notes, escalation template used | Missing notes, wrong priority, or escalation without evidence |
| Ownership | 10% | Followed up on escalations, confirmed the fix, linked or wrote a KB article | Ticket went quiet while waiting on another team |

A score of 1 means the dimension was missing or harmful. A score of 3 means solid with small gaps.

## Auto-Fail

Some mistakes make the ticket score 0 regardless of the rest:

- Customer secrets, API keys, or personal data pasted into a ticket, Slack thread, or escalation
- Incorrect guidance that caused customer impact
- A P1 that was not escalated to on-call

An auto-fail is handled privately in a 1:1. Then ask whether a tool could prevent it, for example secret scanning on ticket replies or the sanitizer in `app/triage.py`. A repeat auto-fail is a process problem before it is a performance problem.

## Using the Results

- **Team level:** the lowest-scoring dimension across the team becomes next month's training topic.
- **Individual level:** the lowest dimension per engineer becomes one coaching goal, with an example ticket to discuss.
- **Positive signal:** high scorers are asked to pair, mentor, or write KB articles. Recognition is part of the framework, not an extra.
- **Not for ranking:** QA scores are a coaching input. They are read together with ticket mix and context, never as a leaderboard.
