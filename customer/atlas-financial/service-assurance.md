# Service assurance, cost model and acceptance

**Fictional service planning.** Targets are proposed exercise expectations.
Historical lab measurements are not a production SLA, financial promise or
claim that a continuously staffed service exists.

## Metrics and reporting contract

| Metric | Formula / measurement scope | Interpretation and exclusion |
|---|---|---|
| Approved batch completeness | Observed distinct expected IDs / approved expected IDs | The AMA pilot measured 10/10; duplicates count separately. This says nothing about all host logs. |
| Duplicate fraction | (total observed events - distinct original IDs) / total observed events | Undefined when total is zero; an envelope retry with identical original lineage is not a new action. |
| Parse conformance | Valid schema rows / all evaluated rows | Synthetic dataset measurement is not real telemetry quality. |
| Ingestion latency | Ingestion observation time minus original event time; report p50/p95 only with sufficient samples | Negative values indicate clock/data error. Historical nine-event averages are not an SLA. |
| Source freshness | Snapshot age and last event age against the source's collection policy | Quiet AzureActivity and intentionally stopped Linux do not require periodic activity. Unknown query evidence is not zero events. |
| Configuration agreement | Reviewed managed properties matching actual REST / all reviewed properties | Does not establish rule execution, connector completeness or data arrival. |
| Deployment reliability | Successful completed authorized deployments / completed attempts, for a named period | Exclude offline PR validations and document abandoned/partial attempts. No current percentage is fabricated. |
| Case acknowledgement | Owner acknowledgement time minus intake time | Synthetic clock values demonstrate calculation only; no real response performance is claimed. |
| Investigation lead time | Evidence-backed classification time minus intake time | Paused waiting-for-evidence intervals must be shown rather than hidden. |
| Approval waiting time | Decision time minus request time | Separates automation execution from human decision delay. |
| Real-data false-positive rate | Demonstrably incorrect real findings / reviewed real findings | Not measured in this lab. Synthetic benign matches are not a production estimate. |
| Billable-volume estimate | Measured billable bytes / agreed GB divisor x explicitly labeled planning rate | Incomplete prices/tiers and billing delays mean this is not a final invoice. |

The reporting record must contain period/timezone, source and query window,
sample counts, evidence class, freshness, failed/partial requests, exclusions,
unknowns, owner and follow-up. A dashboard without these fields can conceal a
collection gap. Proposed P1/P2/P3 acknowledgement targets for a tabletop
exercise are 15/60/240 minutes while that exercise is staffed; they are not
an operating commitment and require a real rota before adoption.

## Budget and retention decisions

Use the actual subscription state, spending protection, available credit,
expiry and cost evidence before cloud work. The user's ceiling is a maximum,
not an amount that must be consumed. A closed credit balance may lag usage;
daily caps and budget alerts are not guaranteed hard monetary limits.

The existing workspace baseline is West Europe, `pergb2018`, 30-day retention
and 0.1 GB/day cap. Preserve those controls. The published AMA pilot contains
900 message bytes but **2,600 billable bytes**, demonstrating why message
payload size is not a billing limit. The monetary charge was not measured.
Do not multiply a hypothetical price by only payload bytes and call the result
a guaranteed maximum. No new paid add-on, VM or SaaS is necessary for this
customer package; its validator and demonstrations operate locally.

Before each proposed live increment, record projected volume, all applicable
meters, query/retention/automation assumptions, duration, stop conditions,
already-running workloads, billing delay margin and source of price evidence.
If availability or cost cannot be bounded sufficiently, retain the offline
demonstration. Do not change billing plan or remove the spending limit.

## Risk register

| ID | Risk / consequence | Control and owner | Residual decision |
|---|---|---|---|
| AF-R01 | Disabled rules give a false impression of active protection | README/catalog labels; detection owner | Accepted lab limitation; no operational protection claim. |
| AF-R02 | Synthetic evidence mistaken for a real incident | Evidence-class fields, lineage and export labels; analyst | Every synthetic ticket/case remains explicitly fictional. |
| AF-R03 | Late billing exceeds a naive estimate | Stop unnecessary cloud work; fresh credit/expiry review; operator | Final monetary cost remains unknown until posted; avoid paid additions. |
| AF-R04 | Existing tenant privileges expose unrelated university data | Owned source only, exact scope, no directory export/device join; cloud owner | Tenant authentication still applies; never equate subscription ownership with tenant authority. |
| AF-R05 | Compromised authorized workflow abuses additive permissions | Immutable trust, protected main/environment, exact role audit and fixed payload guards; platform owner | Main administration remains sensitive; narrow grants do not cancel old ones. |
| AF-R06 | Clock errors or Caller ambiguity corrupt correlation | Explicit UTC offsets, canonical mappings, negative-latency and conflicting-duplicate rejection; detection owner | Unknown/unmapped identities must stay explicit. |
| AF-R07 | Stopped VM appears unhealthy or resumes unapproved collection | Maintenance-aware policy, keep powered off, no autostart; operator | Installed services/DCR resume at boot; do not start casually after the approved pilot. |
| AF-R08 | Replaying an uncertain sender duplicates ingestion/spend | Persistent consumed batch ledger and aggregate reconciliation; platform owner | Do not reset ledgers automatically. |
| AF-R09 | A live incident lifecycle is inferred from local case output | Require separate actual cloud/runtime evidence; detection owner | Local case closure alone cannot close this gate. |
| AF-R10 | Private state or raw screenshots leak identifiers | Ignored private paths, sanitized evidence and staged review; repository owner | Public copies cannot be reliably recalled. |
| AF-R11 | Promotional expiry removes the live demonstration | Offline reproducible replay and preserved actual evidence; operator | No upgrade or subscription switch to preserve the demo. |
| AF-R12 | “Rollback” deletes unrelated resources or weakens access | Exact before-state/ETag, review and no deletion-by-default; platform owner | Account closure is an explicit operator action, not an automated script. |

## Customer acceptance checklist

The [machine-readable contract](acceptance.json) maps twenty deliverables to
usable artifacts. Package validation checks their presence; it does **not**
certify production operations. Before a real service sign-off, require:

- Agreed source/legal scope, owners, support hours and incident authority.
- Source delivery and parsing proof for each live source, with current evidence.
- Explicit active/disabled status and actual runtime proof for every active claim.
- Identity/scope join validation, legitimate-match controls and tuning rationale.
- Reproducible case workflow, recorded human decisions and failure recovery.
- Exact access inventory, cost/retention assumptions and documented unknowns.
- Review of all residual risks, escalation routes, operator handover and closure.

For this personal lab, acceptance is **an engineering deliverable**, not an
assertion that Atlas Financial received a real service. The original mission's
real scheduled alert/incident lifecycle remains a separate evidence requirement
unless the current global project status links an actual completed test.

## Final release checkpoint

The dedicated actual Sentinel lifecycle is now accepted: one explicitly synthetic
row produced a real scheduled alert/incident, was investigated read-only and
closed through exact-incident OIDC. Twelve security definitions stayed disabled;
all 12 KQL bodies also executed in a bounded aggregate. Local case/ticket examples
remain fictional and separate. Compiler-to-live verification matched17 targets
and left2 unqueried. [Final acceptance and evidence](../../docs/validation/project-completion.md).
Keep the portable archive before operator-led personal Azure subscription
closure; leave the university identity/tenant untouched.
