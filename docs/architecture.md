# Architecture

This project uses two small local pipelines so the workflow is easy to inspect. Incident triage works one ticket at a time. Support ops metrics looks at the whole queue, the way a support lead runs a weekly review. Both use only the Python standard library and write JSON and Markdown that static dashboards read.

## Incident Triage Flow

```text
sample incident data
        |
        v
sanitization
        |
        v
runbook signal matching
        |
        v
baseline metric comparison
        |
        v
triage result JSON and summary Markdown
        |
        v
static dashboard
```

## Support Ops Metrics Flow

```text
ticket CSV + SLA policy        QA review CSV + rubric
        |                               |
        v                               v
SLA outcome per ticket          weighted QA scores
(met / breached / pending)      (with auto-fail rules)
        |                               |
        +---------------+---------------+
                        v
  weekly trend, priority and category breakdowns,
  systemic issue detection, engineer coaching view
                        |
          +-------------+--------------+
          v                            v
metrics JSON                  weekly review Markdown
          |
          v
static dashboard
```

## Components

### app/triage.py

The triage engine. It loads incidents and runbooks, masks sensitive values, scores matching evidence, evaluates baseline outliers, and writes output files.

### app/support_ops.py

The support ops engine. It loads tickets and QA reviews, decides SLA outcomes per ticket, builds weekly, priority, customer tier, category, and engineer views, flags systemic issues, scores QA reviews against the rubric, and writes `output/support-ops-metrics.json` and `output/weekly-support-review.md`. It reuses the JSON helpers from `app/triage.py`. Metric definitions are in `docs/support-ops-metrics.md`.

### data/sample_incidents.json

Fictional incidents with ticket notes, log snippets, endpoint metrics, and IAM evidence.

### data/support_tickets.csv and data/qa_reviews.csv

Six weeks of fictional tickets and 30 QA reviews, generated with a fixed seed by `scripts/generate_support_data.py` so numbers and screenshots stay stable.

### data/sla_policy.json and data/qa_rubric.json

SLA targets per priority, the attainment goal, systemic issue thresholds, and the QA rubric dimensions and weights. Teams tune these without changing Python code.

### runbooks/

Each runbook is JSON so support teams can tune signals, thresholds, owners, and actions without changing Python code.

### dashboard/index.html

The triage dashboard. It displays embedded sample results by default. After the demo runs locally, it reads `output/triage-results.json`.

### dashboard/support-ops.html

The support ops dashboard. Locally it reads `output/support-ops-metrics.json` and falls back to `examples/support-ops-metrics.json`. It links to the triage dashboard and back.

### docs/ (GitHub Pages)

`docs/index.html` and `docs/support-ops.html` are published copies of the two dashboards, and `docs/support-ops-metrics.json` is a copy of the example metrics. On the published site the dashboards use only these committed files.

## Design Choice

The project is intentionally local-first. That keeps the demo safe, cheap, and easy to run during an interview or portfolio review.
