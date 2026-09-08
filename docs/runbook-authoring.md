# Runbook Authoring

Runbooks are JSON files stored in `runbooks/`.

Each runbook contains:

- A title and owner
- Required evidence sources
- Matching signals
- Baseline metrics
- Recommended actions
- Escalation guidance

## Signal Example

```json
{
  "name": "Low free disk",
  "keywords": ["disk free", "free space", "low free disk"],
  "weight": 12,
  "rationale": "Low free disk is a direct cause of write failures."
}
```

Signals answer: does the evidence point to this runbook?

## Baseline Example

```json
{
  "key": "free_disk_percent",
  "name": "Free disk space",
  "threshold": 15,
  "direction": "min",
  "unit": "%",
  "rationale": "Workstations below 15 percent free disk should be reviewed."
}
```

Baselines answer: is the observed metric outside normal range?

## Practical Guidance

Good runbooks should avoid vague checks. Use evidence that an engineer can actually collect:

- Log event
- Monitoring alert
- Endpoint health metric
- IAM export field
- Ticket impact statement
- Change window note

The best runbooks make ownership clear and reduce back-and-forth between teams.
