# SentinelOps MXDR project status

Last updated: **3 November 2026**. Read this file first when resuming.
**All eight engineering phases are delivered and accepted within the v1.0.0
lab scope.** Atlas Financial is fictional; this is a personal engineering lab,
not active production monitoring.

The [release and portable artifact](https://github.com/miguelcastu/SentinelOps-MXDR/releases/tag/v1.0.0)
record the final source/merge, required checks and artifact digest. Publication
follows the final protected PR checks.

## Acceptance by phase

| Phase | Accepted proof | Scope boundary |
|---|---|---|
| 1. Detection and incident lifecycle | Twelve deployed disabled definitions, sixty controls, actual execution of twelve KQL queries, and a real scheduled test alert/incident investigated and closed as BenignPositive | Dedicated synthetic test event; no activation of the twelve security rules or production-accuracy claim |
| 2. Ingestion | Actual AzureActivity arrival and ten unique owned Linux AMA/Syslog messages; offline schema, normalizer and bounded client | VM stopped; native SSH and the optional synthetic-authentication custom table are not onboarded |
| 3. Platform health | Three-source policies, sixteen safe faults, maintenance/stale/partial-evidence handling and actual metadata audits | Unmeasured live telemetry remains Unknown |
| 4. Risk correlation | Canonical joins, original-event lineage, strict sequence, decay/caps/deduplication and nine scenarios | Synthetic investigation; scores are not calibrated probabilities |
| 5. SOAR | Durable case, notes/enrichment, reviewer decision, classification, idempotent ticket, audit and six failure scenarios | Local roles/connectors are simulated; no paid SaaS, Logic App or containment |
| 6. IaC and CI/CD | Four compiled Bicep models, one parameter file, nineteen-target preview and six OIDC GETs establishing 17 matches and 2 unqueried references | Nonmutating contract comparison; no full ARM deployment/what-if |
| 7. Customer operations | Twenty deliverables, twelve definition-matched coverage records, eight fictional tickets, RACI, SLIs, risks and handover | No real customer or service certification |
| 8. Portfolio delivery | One-command explorer, portable archive/manifest, timed demonstrations, interview material and protected CI/release | Operates offline after Azure closure; cloud evidence remains dated |

## Actual scheduled-alert lifecycle

On 3 November, the labeled inline event at **19:12:41 UTC** produced one KQL
match and one actual Azure Sentinel / Scheduled Alerts alert at **19:19:09**.
One linked incident was investigated read-only, then classified through OIDC as
**Closed / BenignPositive / SuspiciousButExpected at 19:33:13**. The dedicated
test is disabled and the original thirteen rule properties are unchanged.
A Defender incident URL exists; the Defender portal UI was not opened.
[Full timeline and evidence](validation/lifecycle.md).

The first enable failed because query-execution permission was missing. The
reviewed correction added only workspace `query/read`, with no table-data grant.
Recovery required the prior query's exact digest. The backend then produced the
alert and incident, but detailed-alert observation was denied to CI. The approved
personal MFA session performed that investigation read-only; CI observation was
limited to incident/rule metadata instead of broader entity access.

The original closure PUT omitted the incident activity timestamps. A final,
source-backed reconciliation restored both to **19:12:41 UTC** on the already
closed incident. [OIDC run 41709469491](https://github.com/miguelcastu/SentinelOps-MXDR/actions/runs/41709469491)
verified the result at **20:07:05**. This reconciliation used **one exact-incident
PUT followed by read-back**; it was not a purely read-only run. It did not
reactivate the rule, create a new event or change the classification.

Evidence: [original classified closure](https://github.com/miguelcastu/SentinelOps-MXDR/actions/runs/41704210239),
[detailed investigation](../evidence/completion/alert-investigation.sanitized.json),
[final reconciliation](../evidence/completion/lifecycle-start.sanitized.json),
[closure response](../evidence/completion/lifecycle-close.sanitized.json).
The records share the original query reference; investigation and reconciliation
also share a hashed incident reference. Personal MFA was used for authorized
setup and read-only verification; resource changes used protected-main OIDC.
Failed execution/observation checkpoints remain documented.

## Final Azure, cost and access state

- The same pinned subscription and plan remain Enabled, with spending limit On.
  Published credit is EUR 175.99436818021823, expiring 12 November 2026 at
  18:00:16 UTC. It can lag usage; the final monetary charge remains unknown.
  The operator's EUR 175 maximum was a ceiling, not a spending target.
- The West Europe workspace remains `pergb2018`, with 30-day retention and a
  0.1 GB/day cap. Existing features, access settings, diagnostics and budgets
  are preserved. No paid add-on, Azure compute, university log collection or
  new live ingestion batch was introduced for completion.
- There are **14 unique rules**: twelve managed disabled definitions, the disabled
  LAB test and original enabled Fusion. All original thirteen rule properties
  are preserved. The exact test incident is closed with one linked alert.
- The same CI identity and immutable federation remain. **22 assignments across
  10 custom roles** were independently checked: the original eighteen pairs plus
  four exact lifecycle assignments. No wildcard, table-data, broad writer or
  CI role-management grant was added. The [final audit](../evidence/completion/final-preservation.sanitized.json)
  passed 76 checks: 74 baseline/preservation checks plus two incident-timeline
  checks verified after reconciliation at **20:10:19 UTC**.
- The owned guest is **powered off**; Arc Disconnected is expected. The AMA pilot
  and one-time initialization ledgers remain consumed. There is no auto-start
  or recurring sender.
- [GitHub closeout](../evidence/completion/github-closeout.sanitized.json) removed
  the lifecycle approval gate, recovery/reconciliation references and exact-incident
  identifier secret. Existing Azure OIDC secrets, main-only environment and
  branch protections remain unchanged. The test is disarmed; all 22 Azure
  assignments remain in place.

## Verification and delivery

The source suite contains **213 passing local tests**. Other checks cover the
restricted detection contracts, sixty portfolio controls, sixteen health faults,
nine risk scenarios, one synthetic case with nine audit events/one ticket and
six failure scenarios, actual compilation of four Bicep models/one parameter
file, and twelve customer coverage records/twenty deliverables/eight tickets.
Required Python 3.12 CI, actionlint, independent SOAR schema checks, links,
browser behavior and artifact/privacy reviews support release delivery.

One actual one-hour aggregate POST executed all twelve KQL queries:
AZ-DET-002 matched 3 rows, AZ-DET-003 matched 2, and the other ten matched 0.
This is runtime proof, not precision/recall or a false-positive rate.
[Actual KQL evidence](../evidence/completion/live-kql.sanitized.json).
The [compiler-to-live OIDC run](../evidence/completion/infrastructure.sanitized.json)
verified 17 Matching, 0 Drift, 0 Missing and 2 Unknown through six GETs, without
resource writes, log queries, role changes or a VM start.

Protected delivery: [PR #20](https://github.com/miguelcastu/SentinelOps-MXDR/pull/20)
implemented the offline portfolio; [PR #21](https://github.com/miguelcastu/SentinelOps-MXDR/pull/21)
added the minimum query gate and contract verification; [PR #22](https://github.com/miguelcastu/SentinelOps-MXDR/pull/22)
added bounded aggregate KQL; [PR #23](https://github.com/miguelcastu/SentinelOps-MXDR/pull/23)
added metadata observation. The final evidence PR/release records the final-head
CI and merge. Earlier pending states remain historical in dated records and Git
history; this acceptance supersedes them.

## Handover and scope freeze

Run `python -m lab --bundle` and open `.local/lab/index.html`. Preserve the
portable archive/manifest and a local clone before operator-led Azure closure.
Private keys, pins and ledgers are separate from public release assets.
[Complete acceptance](validation/project-completion.md), [reviewer guide](portfolio/README.md),
[customer handover](../customer/atlas-financial/handover.md).

No required engineering task remains within the accepted lab scope. Do not
reactivate the completed test, reset ledgers, reconnect/start the guest or expand
collection under consumed approvals. Production/native-source work, active
rule tuning, paid services or full platform deployment require a new scope and
valid credit. After expiry, preserve the release rather than switching or
upgrading. Subscription cancellation is the operator's action; this project
has not deleted Azure resources or the account, and must not affect the
university identity or directory.
