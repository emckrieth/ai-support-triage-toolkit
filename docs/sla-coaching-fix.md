# SLA coaching: distinguish pending outcomes from breaches

## Problem and correction

The coaching report used `(first_response_sla_percent or 0) < goal`. When all tickets were still inside their first-response deadlines, attainment was None (no eligible outcomes), but the report treated it as 0% and issued a low-attainment coaching warning.

The correction explicitly checks that attainment is not None before comparing it with the goal. Genuine 0% attainment still triggers the warning. The underlying attainment calculation and policy targets are unchanged: attainment is met / (met + breached), excluding pending outcomes.

## Regression cases

All cases use the configured P2 60-calendar-minute first-response target.

| Case | Input | Expected result |
| --- | --- | --- |
| Pending | No response, report 30 minutes after creation | None attainment; no first-response coaching warning |
| Breached | Response at 90 minutes, report at 120 minutes | 0% attainment; first-response coaching warning |
| Met | Response at 30 minutes, report at 120 minutes | 100% attainment; no first-response coaching warning |

## Verification and attribution

On October 22, 2026, the owner ran a small attainment exercise and observed 50.0 for mixed outcomes, None for all-pending outcomes, and 0.0 for all-breached outcomes. With Codex guidance, the owner manually applied the explicit None check, corrected an indentation error, added AI-supplied regression tests and ran the tests locally. The 12 support-operations tests passed.

Codex then substituted the original coaching logic in memory and ran the three new regression tests. Only the pending-outcome case failed, demonstrating that the test catches the original bug. This did not alter saved source files. The complete 15-test repository suite passed with the saved fix.

Reproduce the complete suite from the repository root:

```powershell
python -m unittest discover -s tests -v
```

This is evidence of a guided correction and hands-on verification, not independent authorship of the original module or tests. Existing Claude attribution is retained. A subsequent assistant-executed correction completed the weekly-trend issue. The old `or 100` expression treated a genuine 0% week as 100% and could select a 50% week instead. The corrected comparison excludes None, retains zero and safely handles an all-pending report. Three regression tests cover zero versus fifty/pending, all-pending weeks and weeks meeting the goal. Before the correction, the zero-attainment case failed; afterward all 18 repository tests passed. The owner delegated this second correction to Codex; it is not recorded as a personal edit or run.
