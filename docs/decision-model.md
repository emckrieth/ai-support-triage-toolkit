# Decision Model

This project recommends a runbook by comparing an incident against three types of evidence:

- text signals from ticket notes and logs
- metric outliers compared with baseline thresholds
- required evidence sources for the runbook

The score is a confidence value from 0 to 100. A higher score means the incident evidence is a stronger match for that runbook.

## Score Inputs

### Evidence Signals

Each runbook includes words and phrases that commonly appear when that issue is present. Examples include `vpn`, `packet loss`, `mfa`, `privileged`, `disk`, and `free space`.

When those signals appear in the incident summary, ticket notes, or log snippets, the runbook score increases.

### Baseline Outliers

Metrics are compared with practical support baselines. Examples:

- free disk below 15 percent
- packet loss above 1 percent
- VPN reconnect attempts above 3
- privileged access review older than 90 days
- verification evidence older than 24 hours

Outliers help explain why a runbook is relevant. They also help separate real issues from normal noise.

### Evidence Coverage

Each runbook lists the evidence sources an engineer would usually want before acting. Missing evidence lowers confidence and is shown clearly in the dashboard.

## How to Interpret Scores

| Score | Meaning | Support action |
| --- | --- | --- |
| 85 to 100 | Strong match | Follow the runbook and document evidence |
| 70 to 84 | Likely match | Follow the runbook, but review missing evidence |
| 50 to 69 | Partial match | Continue triage before remediation |
| Below 50 | Weak match | Do not rely on the recommendation |

## Why This Matters

Support teams need decisions that are explainable. A useful recommendation should show:

- what evidence was used
- what baseline was exceeded
- what evidence is missing
- which team should own the next step

That keeps the workflow practical for incident response, escalation, and problem review.
