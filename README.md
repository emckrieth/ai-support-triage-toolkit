# AI Support Triage Toolkit

AI Support Triage Toolkit is a local-first support engineering project that turns tickets, logs, and endpoint or identity evidence into sanitized summaries, baseline outlier checks, runbook recommendations, and an interactive dashboard.

The goal is to show practical enterprise support skills:

- Evidence-based incident triage
- Baseline metric comparison for endpoint, network, and IAM issues
- Runbook recommendation logic
- Sanitization before sharing logs or using AI workflows
- Clear escalation notes for support, infrastructure, endpoint, and IAM teams

## What This Solves

Support teams often receive messy ticket notes, screenshots, log snippets, endpoint health data, and identity exports. This project simulates a safer workflow:

1. Load incident evidence from JSON.
2. Mask sensitive values such as emails, private IPs, hostnames, user IDs, and session IDs.
3. Compare observed metrics against enterprise-style baselines.
4. Score which runbook best matches the evidence.
5. Generate a triage result, escalation note, and dashboard data.

## Quick Start

```powershell
python -m app.triage --input data/sample_incidents.json --runbooks runbooks --output output/triage-results.json --summary output/support-summary.md
python -m unittest discover -s tests
python -m http.server 8000
```

Then open:

```text
http://localhost:8000/dashboard/
```

The dashboard includes sample results for quick review. After you run the triage command, it loads the generated `output/triage-results.json` file.

On Windows, you can also run:

```powershell
.\scripts\run_demo.ps1
```

## Two-Minute Demo

1. Run `.\scripts\run_demo.ps1`.
2. Start the local web server with `python -m http.server 8000`.
3. Open `http://localhost:8000/dashboard/`.
4. Select each incident in the left panel and review the recommended runbook, baseline outliers, evidence coverage, and escalation notes.
5. Open `output/support-summary.md` to see the support-ready summary generated from the same data.

## Dashboard Preview

The dashboard is designed for quick operational review. It shows:

- incident priority and next owner
- runbook confidence score
- baseline metric comparisons
- evidence sources used for the recommendation
- sanitized ticket notes and escalation details

This helps a support engineer explain why a runbook was selected instead of only showing a final recommendation.

## Example Scenarios

The sample data includes three support scenarios:

- Remote users cannot connect to VPN
- Endpoint disk pressure causing application failures
- MFA reset request with stale privileged access

Each scenario includes ticket notes, technical evidence, observed metrics, and expected ownership.

## How Runbook Matching Works

Each runbook defines:

- Evidence signals and keywords
- Baseline metrics and thresholds
- Required evidence sources
- Recommended actions
- Escalation owner

The tool does not pretend to replace an engineer. It organizes evidence so an engineer can make a faster and safer decision.

For more detail, see `docs/decision-model.md`.

## Baseline Metrics

The baseline checks use practical operating thresholds that are common in large support environments. They are not universal company policy. They are examples a support engineer can tune for their own environment.

Examples:

- Free disk below 15 percent is actionable
- Packet loss above 1 percent is abnormal
- Internal DNS lookup time above 300 ms is suspicious
- Privileged access review older than 90 days needs IAM review
- Verification evidence older than 24 hours should be refreshed

## Project Structure

```text
ai-support-triage-toolkit/
├── app/
│   ├── __init__.py
│   └── triage.py
├── dashboard/
│   └── index.html
├── data/
│   └── sample_incidents.json
├── docs/
│   ├── architecture.md
│   ├── decision-model.md
│   ├── metrics-baselines.md
│   └── runbook-authoring.md
├── examples/
│   └── sample-output.md
├── runbooks/
│   ├── endpoint-disk-pressure.json
│   ├── iam-mfa-privileged-review.json
│   └── vpn-remote-access.json
├── scripts/
│   └── run_demo.ps1
├── tests/
│   └── test_triage.py
├── .gitignore
├── LICENSE
└── pyproject.toml
```

## Why This Is Relevant

This repo demonstrates skills that map to systems, support, and IAM engineering roles:

- Troubleshooting from evidence instead of guessing
- Knowing when a metric is an outlier
- Writing reusable operational runbooks
- Protecting sensitive data before sharing
- Creating clear escalation notes
- Building useful automation around real support workflows

## Safety Note

All sample data is fictional and sanitized. Do not commit real production logs, customer data, private IP ranges from a real employer, tokens, secrets, or internal hostnames.
