# Severity Levels and On-Call

An example framework for a support team serving an API platform with enterprise customers across time zones. Ticket priority (P1-P4) drives the SLA clock. Incident severity (SEV1-SEV3) is declared when one problem affects many customers or a core service.

## Ticket Priority

| Priority | Meaning | Example | First response | Resolution |
| --- | --- | --- | --- | --- |
| P1 | Production down or decisions failing | API returning 5xx for all requests; webhooks not delivered for any customer | 15 min | 4 h |
| P2 | Major feature degraded, painful workaround | Elevated latency on one endpoint; delayed webhooks for one customer | 60 min | 24 h |
| P3 | Question or partial issue with a workaround | Unexpected score on a single transaction; SDK integration question | 4 h | 72 h |
| P4 | How-to, feature request, cosmetic | Dashboard filter request; documentation typo | 8 h | 5 days |

Customers sometimes over- or under-state priority. Support sets the final priority from impact evidence and says why in the first reply.

## Incident Severity

| Severity | Trigger | Who is paged | Customer updates |
| --- | --- | --- | --- |
| SEV1 | Core API or decisioning unavailable or wrong for many customers | Support on-call, Engineering on-call, incident commander | Status page within 15 min, then every 30 min |
| SEV2 | Partial outage, one region or feature, or several enterprise customers affected | Support on-call and Engineering on-call | Status page within 30 min, then every 60 min |
| SEV3 | Degradation with a workaround, single customer, or internal tooling | Business hours owner | Direct updates to affected customers |

Declare early. Downgrading a SEV2 to a SEV3 costs little; finding out an hour late that it was a SEV1 costs customer trust.

## Support On-Call

**Coverage.** Follow-the-sun across regions where possible. Every hour of the week has a named primary and a named secondary. A gap in the schedule is itself an incident risk; the week of 2026-09-21 in the sample data shows what a thin rotation does to P1 and P2 response times.

**Primary on-call**

- Acknowledges P1 tickets and pages within 5 minutes
- Decides whether a P1 is an incident and declares the severity
- Opens the incident channel, posts the first status update, and pulls in Engineering on-call
- Keeps a timeline: what was seen, when, and what was done

**Secondary on-call**

- Covers the queue while the primary works the incident
- Takes over if the primary does not acknowledge within 10 minutes

**Handoff** at every shift change uses one written note:

```text
Open incidents and their owners
P1/P2 tickets in flight and the next promised update time
Anything waiting on Engineering, with ticket links
Known noisy alerts or customers to watch
```

## Escalation Paths

| Escalate to | When | Include |
| --- | --- | --- |
| Engineering on-call | Suspected platform bug, outage, or data integrity issue | Request IDs, timestamps (UTC), endpoint, payload sample with secrets removed, customer impact, what was ruled out |
| Product | Repeated how-to questions, missing capability, confusing behavior that works as designed | Ticket links, count, customer tier mix, suggested change |
| Customer Success | Account risk, contract or SLA credit discussion, executive sponsor contact | Timeline, business impact, what the customer was told |
| Support lead | SLA at risk on P1/P2, angry enterprise customer, unclear owner | Ticket link and what decision is needed |

## After an Incident

1. Within one business day: customer-facing summary for affected enterprise customers.
2. Within five business days: post-incident review with timeline, root cause, contributing factors, and action items with owners.
3. Support-specific actions: update runbooks, add a macro or KB article, and add a detection rule if support saw the problem before monitoring did.
4. Review the weekly metrics the following week to confirm the category volume returned to baseline.
