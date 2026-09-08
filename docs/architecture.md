# Architecture

This project uses a small local pipeline so the workflow is easy to inspect.

## Flow

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

## Components

### app/triage.py

The main engine. It loads incidents and runbooks, masks sensitive values, scores matching evidence, evaluates baseline outliers, and writes output files.

### data/sample_incidents.json

Fictional incidents with ticket notes, log snippets, endpoint metrics, and IAM evidence.

### runbooks/

Each runbook is JSON so support teams can tune signals, thresholds, owners, and actions without changing Python code.

### dashboard/index.html

A static dashboard that reads `output/triage-results.json` after the demo runs.

## Design Choice

The project is intentionally local-first. That keeps the demo safe, cheap, and easy to run during an interview or portfolio review.
