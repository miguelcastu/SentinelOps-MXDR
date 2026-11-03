# Fifteen-minute technical presentation

Suggested title: **SentinelOps MXDR: engineering a bounded, testable Sentinel lab**.
Audience: platform, detection and SOC engineering reviewers. Atlas Financial
is fictional; there is no association with a commercial security provider.

| Slide / time | Technical content | Proof to open | Question the reviewer should be able to answer |
|---|---|---|---|
| 1. Problem and constraints, 0:00-1:00 | Build an auditable engineering portfolio with limited promotional credit, an existing subscription and no university telemetry. Prefer local repeatability. | [Project status](../PROJECT_STATUS.md) | Which outcomes required cloud evidence and which could stay local? |
| 2. Architecture, 1:00-2:30 | Subscription source versus tenant authorization versus workspace destination; AzureActivity export; owned local AMA path; independent GitHub control plane. | [Architecture](../architecture/overview.md), [source catalog](../../customer/atlas-financial/service-design.md) | Where do events originate, and what exactly is collected? |
| 3. Detection engineering, 2:30-4:30 | Twelve fixed disabled rules; precise status/operation predicates; entity ambiguity; ID preservation; ten-minute failure bin and strict fifteen-minute cross-event sequence. | [Catalog](../detections/portfolio.md), [AZ-DET-012](../../detections/azure/AZ-DET-012.kql) | What does a match prove, and which benign activities still match? |
| 4. Correlation and confidence, 4:30-6:00 | Explicit identity mapping; bounded scoring/decay/caps; ordered sequence; maintenance controls; health uncertainty separate from risk. | [RBA design](../operations/risk-correlation.md), local replay | Why does a multi-stage chain matter more than isolated low-confidence events? |
| 5. Case orchestration, 6:00-7:30 | Evidence-linked intake, persistent state, dedup/conflict protection, enrichment, human gates, audit and bounded failure recovery. | Local case demonstration and its validation record | What happens on duplicate delivery, a timeout or an unapproved action? |
| 6. Platform reliability, 7:30-9:00 | Event-driven quiet sources, single approved batches, Unknown evidence, latency/clock/schema errors and local fault injection. | [Health operations](../operations/platform-health.md), fault dashboard | Can the system distinguish missing telemetry from unavailable measurement? |
| 7. CI/CD and infrastructure, 9:00-10:30 | Offline PR checks versus protected OIDC; fixed resources, ETag/create guards, complete read-back; compiler/preview/deployment evidence distinctions. | [Security](../security.md), workflows and IaC validation | What prevents an arbitrary resource or enabled rule from being deployed? |
| 8. Real engineering failures, 10:30-12:00 | Policy remediation, nonexistent-resource RBAC, read-only DCR metadata, asynchronous AMA provisioning and config propagation. | [Case studies](engineering-case-studies.md) | How was each failure diagnosed without widening permissions or cost? |
| 9. Service delivery and economics, 12:00-13:30 | Source ownership, RACI, operating handover, eight tickets, metrics denominators and explicit cost uncertainty. | [Customer assurance](../../customer/atlas-financial/service-assurance.md), tickets | Could another engineer operate and honestly report this system? |
| 10. Results and limits, 13:30-15:00 | Dated actual OIDC/REST and ten-message Syslog proof; reproducible offline integration; disabled coverage; live acceptance status; account-independent demo. | [Acceptance checkpoint](../PROJECT_STATUS.md), actual evidence and final validation | Which claims are verified, synthetic, historical or still unexecuted? |

## Discussion prompts

- Why keep AzureActivity Caller as context instead of asserting a canonical Account?
- How can overlapping scheduled windows duplicate a real action across alerts?
- Why does `finally` not guarantee cloud-state restoration after runner loss?
- What can exact resource RBAC enforce, and what still depends on payload review?
- Why does a 900-byte payload produce 2,600 billable bytes in the real pilot?
- What changes before this lab could serve a real regulated financial customer?

For the final prompt, cover current data/permissions, actual alert runtime,
privacy/legal review, a staffed operating model, incident authority, recovery
testing and independent cost governance. Do not present a polished lab UI as
evidence that those production requirements have been satisfied.

## Final release checkpoint

The dedicated actual Sentinel lifecycle is now accepted: one explicitly synthetic
row produced a real scheduled alert/incident, was investigated read-only and
closed through exact-incident OIDC. Twelve security definitions stayed disabled;
all 12 KQL bodies also executed in a bounded aggregate. Local case/ticket examples
remain fictional and separate. Compiler-to-live verification matched17 targets
and left2 unqueried. [Final acceptance and evidence](../validation/project-completion.md).
Keep the portable archive before operator-led personal Azure subscription
closure; leave the university identity/tenant untouched.
