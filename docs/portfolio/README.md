# Portfolio reviewer guide

Start with the [five-minute demonstration](demo-five-minutes.md), then use the
[fifteen-minute technical presentation](presentation-fifteen-minutes.md) for a
deeper discussion. Both distinguish actual cloud observations, local synthetic
behavior, mocks and designs.

| Reviewer interest | Recommended route |
|---|---|
| Detection engineering | [Twelve-rule catalog](../detections/portfolio.md) -> [customer coverage](../../customer/atlas-financial/detection-coverage.md) -> ordered AZ-DET-012 query -> RBA replay |
| Platform and DevSecOps | [Architecture](../architecture/overview.md) -> [security](../security.md) -> OIDC workflow -> [engineering decisions](engineering-decisions.md) -> actual REST evidence |
| Reliability and troubleshooting | [Health runbook](../operations/platform-health.md) -> local fault dashboard -> [case studies](engineering-case-studies.md) |
| SOC automation | Local case demonstration -> [investigation/change workflow](../../customer/atlas-financial/operations.md) -> structured audit / duplicate and failure controls |
| Customer delivery | [Atlas Financial package](../../customer/atlas-financial/README.md) -> eight tickets -> assurance/risk register -> handover |
| Candidate interview | [Interview and CV](interview-and-cv.md) -> technical presentation questions -> verified/unknown acceptance discussion |

The [authoritative project checkpoint](../PROJECT_STATUS.md) identifies the
latest release scope and actual evidence. Historical Azure screenshots and
JSON records prove observations at their timestamps, not ongoing operation.
The local replay remains useful after the Azure subscription is closed.

## Final release checkpoint

The dedicated actual Sentinel lifecycle is now accepted: one explicitly synthetic
row produced a real scheduled alert/incident, was investigated read-only and
closed through exact-incident OIDC. Twelve security definitions stayed disabled;
all 12 KQL bodies also executed in a bounded aggregate. Local case/ticket examples
remain fictional and separate. Compiler-to-live verification matched17 targets
and left2 unqueried. [Final acceptance and evidence](../validation/project-completion.md).
Keep the portable archive before operator-led personal Azure subscription
closure; leave the university identity/tenant untouched.
