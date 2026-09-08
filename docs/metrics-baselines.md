# Metrics And Baselines

Baseline metrics show whether a device, service, or identity workflow is outside normal operating range.

These values are examples for a lab project. In a real company, they should be tuned to monitoring data, SLAs, risk appetite, and support policy.

## Endpoint Baselines

| Metric | Example baseline | Why it matters |
| --- | ---: | --- |
| Free disk space | At least 15 percent | Low disk can cause patching, logging, and application write failures. |
| Temp growth rate | Under 5 GB per day | Fast recurring growth can point to a repeat problem. |
| Application write failures | Under 5 per hour | Sustained write failures support endpoint remediation. |
| Last reboot age | Under 30 days | Long uptime can increase instability when other symptoms exist. |

## Network And VPN Baselines

| Metric | Example baseline | Why it matters |
| --- | ---: | --- |
| VPN handshake p95 | Under 250 ms | High latency can indicate gateway or network path issues. |
| Tunnel packet loss | Under 1 percent | Packet loss can break voice, SaaS, and remote sessions. |
| Internal DNS lookup | Under 300 ms | Slow resolution after VPN connection can point to tunnel or DNS issues. |
| Authentication failure rate | Under 2 percent | Repeated failures can indicate policy, identity, or gateway problems. |

## IAM Baselines

| Metric | Example baseline | Why it matters |
| --- | ---: | --- |
| Privileged review age | Under 90 days | Stale reviews increase access risk. |
| MFA failures | Under 3 per hour | Multiple failures should trigger verification checks. |
| Approval completeness | 100 percent | Access changes should have complete approval evidence. |
| Verification age | Under 24 hours | Old verification evidence should be refreshed. |

## How To Use These

Baselines should not close tickets by themselves. They help an engineer decide:

- What is abnormal
- What evidence to collect next
- Which team should own the next action
- Whether an incident may be a repeat problem
