# Interview explanation and portfolio wording

Use wording that matches the latest verified evidence. This is a personal
engineering lab with a fictional customer; it is not commercial experience,
an employer engagement or a continuously operating production SOC.

## Ninety-second explanation

“I built SentinelOps MXDR to demonstrate the complete engineering path around
a Sentinel lab: source onboarding, detection code, secure delivery, platform
health, correlation, case workflow and customer handover.

The configuration path uses protected GitHub pull requests, short-lived OIDC
and fixed resource-scoped permissions. I verify the actual persisted Azure
response rather than treating a successful HTTP request or local test as
deployment proof. The detection catalog contains twelve deployed disabled
AzureActivity definitions, including failure bursts and ordered role-change /
diagnostic-change correlation. I document legitimate matches and entity limits.

The risk engine preserves original-event lineage, explicit identity joins,
decay/caps and narrow maintenance context. It sends a labeled fictional
multi-stage finding through a local case demonstration with human decisions
and an audit trail. Source-health uncertainty stays separate from risk.

I also integrated an owned Ubuntu VM through Arc and AMA. One actual bounded
test reconciled ten unique Syslog messages; I stopped the VM afterwards.
The public repo preserves sanitized real evidence alongside reproducible
synthetic tests, operating runbooks and a fictional customer package.
I can reproduce the local demonstration after the promotional subscription
ends, and I state explicitly which live behaviors were not executed.”

## Deeper technical questions

| Question | Grounded answer |
|---|---|
| What does OIDC replace? | A permanent CI client secret. A protected main job receives a short-lived GitHub assertion that Azure checks against exact federation trust; Azure authorization still depends on additive RBAC. |
| Can someone copy the public repository and deploy to your Azure? | Code visibility is not the trust relationship. An arbitrary fork lacks the immutable repository/environment subject and authorized environment context. Compromise of authorized main or administration remains consequential. |
| Why disable detections? | It preserves the approved baseline and avoids claiming unmeasured active protection. Deployment correctness, KQL runtime and alert/incident behavior are separate acceptance dimensions. |
| How did you test KQL? | Fixed text/contracts plus reference-model fixtures cover intended semantics; those Python tests are explicitly not Kusto execution. Actual aggregate queries are recorded separately. |
| How do you control false positives? | Investigate legitimate matches, validate exact actor/scope/change windows and test suspicious lookalikes. I do not equate a fixture pass rate with production precision. |
| What happens when data is missing? | Unknown query evidence is not zero events; quiet event-driven data has no heartbeat obligation. Risk remains visible, while confidence records collection gaps. |
| How is cost controlled? | Local compute, no paid add-ons, bounded batches/queries, preserved caps/spending protections and eligibility checks. The measured billable bytes are not a guaranteed final invoice. |
| What was difficult? | Azure rejected exact RBAC for an absent DCR. I stopped, obtained a single-target bootstrap exception, verified matching resources, then returned to exact-scoped OIDC. |
| What would you change in production? | Formal data/legal authority, operational staffing and escalation, actual alert lifecycle and source-specific tuning, backup/recovery exercises, stronger separation of duties and measured cost/runtime baselines. |

## CV / LinkedIn project entry

**SentinelOps MXDR — personal Microsoft Sentinel engineering lab**

- Engineered twelve AzureActivity detection definitions with synchronized KQL,
  bounded correlation logic, original-event lineage, synthetic controls and
  investigation runbooks; deployed disabled through protected GitHub OIDC.
- Implemented reproducible telemetry normalization, source-health diagnostics,
  entity-risk correlation and a local synthetic case workflow with human gates
  and structured audit evidence.
- Integrated one owned Linux VM using Azure Arc/AMA; reconciled ten actual
  Syslog messages with aggregate-only queries and preserved subscription controls.
- Produced recovery/security guidance, troubleshooting case studies and a
  fictional financial-customer operations package, with actual and synthetic
  evidence clearly distinguished.

Do not add “protected a financial institution,” “24/7 SOC,” “production incident
response,” “100% ATT&CK coverage,” “zero false positives” or “zero Azure cost.”
Only mention a real completed Sentinel alert/incident lifecycle if the final
evidence actually establishes it. Use the current test count from CI rather
than copying an obsolete number into interview material.
