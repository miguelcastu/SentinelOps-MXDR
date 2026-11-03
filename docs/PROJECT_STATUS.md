# SentinelOps MXDR project status

Last updated: **3 November 2026**. Read this file first when resuming. Atlas
Financial is fictional. Current increment: complete the verified offline
portfolio, prepare the isolated real-scheduler acceptance and preserve the
original subscription. **The original mission is not fully accepted while
the real scheduled-alert/incident lifecycle remains unverified.**

| Phase | Current delivered scope | Acceptance boundary |
|---|---|---|
| 1. Detection engineering | Twelve actual disabled rules, sixty portfolio controls, investigations; fixed isolated lifecycle workflow prepared | Actual scheduled alert -> linked incident -> investigation/classified closure still pending its concrete activation/access scope |
| 2. Advanced ingestion | Offline schema/normalizer/transport plus actual AzureActivity and owned AMA/Syslog proofs | Ten unique AMA messages verified; guest stopped. Optional synthetic-auth custom table remains undeployed |
| 3. Platform health | Three-source policies/inventory, sixteen simulated faults, maintenance/stale/partial handling, prior actual read-only OIDC configuration audit | No new live query or automatic AMA telemetry collector; current telemetry/runtime uncertainty remains explicit |
| 4. Risk correlation | Canonical joins, strict sequence, decay/caps/dedup, original lineage and nine replay scenarios | Fully implemented/verified synthetic scope, not a live Sentinel finding |
| 5. SOAR | Durable cases, enrichment/notes, reviewer gates, classified closure, idempotent local ticket, chained audit and six failure scenarios | Fully implemented/verified local scope; remote roles/connectors/timeouts simulated |
| 6. IaC and CI/CD | Four actual compiler-validated Bicep models, one parameter file, nineteen-target comparison, exact/destructive-change guards and recovery runbook | No full platform ARM deployment/what-if claim; existing fixed-resource OIDC evidence stays separate |
| 7. Customer operations | Twenty mapped deliverables, twelve-rule source-derived coverage, eight fictional tickets, RACI/SLIs/risks/acceptance/handover | Fictional package validated offline; no real service/customer certification |
| 8. Portfolio delivery | One-command integrated explorer, source/demo archive and SHA manifest, timed demo/presentation/interview material | Tested local deliverables usable after Azure closes; original full acceptance still depends on Phase1 |

## Current increment: Portfolio completion work

The operator explicitly approved the concrete PR #20 test on 3 November:
"autorizo las pruebas que necesites, cualquiera". Actual OIDC run
[41697635395](https://github.com/miguelcastu/SentinelOps-MXDR/actions/runs/41697635395)
created LAB-VAL-001 disabled, but enable returned Unauthorized because Azure
requires query-execution permission even for an inline datatable. Cleanup and
independent REST confirm disabled; no incident was observed. Original thirteen
rules/settings are preserved. Exact setup reached twenty CI assignments.
The reviewed correction adds only workspace query/read execution, no table
access/DataActions, and one explicit prior-query-digest-bound recovery. No
broad role or personal deployment fallback. The new compiler-to-live verifier
uses only six existing fixed GET routes; actual verification remains pending.
Local suite now includes 198 tests. Live acceptance remains incomplete until
the actual linked alert/incident and classified closure are verified.

- Actual read-only Azure eligibility confirms same Enabled subscription, spending limit On, published EUR175.99436818021823, expiry 12 November 2026 18:00:16 UTC. New operator budget is maximum EUR175, not a spending target. Closed credit can lag usage. [Eligibility](../evidence/completion/eligibility.sanitized.json).
- Fresh REST baseline: West Europe, `pergb2018`, retention30days, cap0.1GB/day, thirteen rules/twelve disabled Scheduled/original enabled Fusion, eighteen CI assignments; Arc Disconnected. No new cloud mutation/log query/message or paid plan for this offline increment. [Actual baseline](../evidence/completion/baseline.sanitized.json).
- `python -m lab --bundle` exercises schema/normalization, sixty detection controls, sixteen health scenarios, nine risk scenarios, the exact RBA finding -> one Closed synthetic SOAR case, nine audit events/one idempotent ticket/six failure scenarios, and a nineteen-target synthetic IaC comparison. Four source-health/risk/evidence views live in `.local/lab/index.html`. Private state is excluded from its portable archive.
- Real locked Bicep0.48.1 compiles four models/one parameters file; exact AMA3/rules12 body comparisons pass. [Compiler evidence](../evidence/completion/bicep-compile.sanitized.json). This does not prove a full platform deployment.
- Local unit suite:187tests; detection/portfolio/customer validation, actual compiler/linter, actionlint, archive/HTML safety, documentation links and identifier/token/key scans. Required Python3.12 CI and exact protected-merge references are recorded in the delivery PR. No Azure workflow is needed for offline delivery.
- [Full acceptance](validation/project-completion.md), [customer package](../customer/atlas-financial/README.md), [reviewer tour](portfolio/README.md), [SOAR runbook](operations/soar.md), [IaC/recovery](deployment/infrastructure.md).
- [Concrete isolated live acceptance](deployment/synthetic-lifecycle.md) is reviewable code with no arbitrary query/target, one self-expiring synthetic datatable event, bounded polls and finally-disable. Activation/new access remain gated under AGENTS.md. Code/tests are not cloud proof and consumed AMA ledgers are untouched.

## Next executable task

Complete required protected PR CI/merge and archive verification. If the
operator approves the concrete isolated synthetic lifecycle exception,
recheck credit/expiry, prepare only exact narrow roles, execute start once
through merged-main OIDC, verify the actual linked alert/incident, disable,
grant classification at only that actual incident, close through OIDC and
record sanitized read-back. Do not broaden permissions if a missing-resource
scope is rejected. No general rule activation, recurring collection, extra
AMA batch, university logs or paid add-on is needed.

If consent, authentication, permissions or subscription eligibility prevent
that acceptance, retain the implemented offline portfolio and report the
precise unaccepted gate. Never mark the original mission complete from the
synthetic case. If Azure has expired, stop new project/cloud work and hand
over existing verified artifacts without upgrade/switch/deletion.

## Historical implementation and cloud checkpoints

The following dated records describe earlier increments. Their counts and
scope apply at those timestamps. Current three-source health-policy integration
supersedes older statements that AMA is outside the inventory; live AMA health
queries are still absent.

## Current increment: Verified personal Linux Arc/AMA pilot

- **Acceptance complete for the approved pilot:** at 21:55:02 UTC on 28 October, actual Kusto returned **10 total / 10 distinct messages**, 2,600 billable bytes, from the single 900-message-byte batch. Two of at most three aggregate queries were used; no raw events were returned and no repeat is authorized. [Ingestion evidence](../evidence/local-linux-ama/ingestion.sanitized.json).
- **The guest is stopped:** graceful shutdown and actual VirtualBox `poweroff` verified at 21:58:02 UTC. Arc/DCR/AMA metadata persists; no Azure compute was created. No schedule or auto-start. [Shutdown evidence](../evidence/local-linux-ama/shutdown.sanitized.json).
- **Actual cloud configuration:** one Arc machine, DCR `dcr-sentinelops-ama-linux`, AMA extension 1.45.1 and association `sentinelops-ama-linux`, all at the reviewed fixed targets. Only local4 Warning and higher to the existing workspace's `Syslog` table; no native SSH/authpriv, directory export or university device join. Association provisioning state is not reported by the API; its actual binding and the successful ingestion are verified separately.
- **Explicit one-time exception used:** Azure rejected RBAC at the absent DCR with 404. The operator approved PR #16's initialization of only DCR/extension/association through the existing personal MFA session. [Actual initialization](../evidence/local-linux-ama/initialization.sanitized.json) completed at 21:41:24 UTC; the completion ledger blocks reuse. Do not rerun the initializer, reconnect Arc or reset the pilot ledger.
- **Routine control stays OIDC:** the existing CI identity/trust was reused with four additional exact assignments: one machine metadata reader and three child-resource writers. Seven verified custom role definitions / eighteen total assignments; no broad writer or new CI query access. The [successful main OIDC run](https://github.com/miguelcastu/SentinelOps-MXDR/actions/runs/40774219658) verified all three resources as already matching, without creating them or sending messages. [OIDC evidence](../evidence/local-linux-ama/oidc-configuration.sanitized.json), [independent preservation/RBAC audit](../evidence/local-linux-ama/preservation.sanitized.json).
- **Subscription and cost controls preserved:** same pinned Enabled subscription, spending limit On, workspace `pergb2018`, 30-day retention and 0.1 GB/day cap. All thirteen rule properties are unchanged: twelve managed disabled and original Fusion enabled. Post-pilot credit API still publishes EUR 175.99436818021823, expiring 12 November 2026 18:00:16 UTC. This balance can lag usage; the pilot's monetary charge is unknown, not proven zero. [Post-pilot financial check](../evidence/local-linux-ama/financial.sanitized.json).
- **Delivery and validation:** local preparation PR #13; fixed cloud tooling PRs #14-16; latest strict DCR read-back fix [PR #18](https://github.com/miguelcastu/SentinelOps-MXDR/pull/18), implementation `31a206a`, merge `e2a2439`, [required Python 3.12 CI](https://github.com/miguelcastu/SentinelOps-MXDR/actions/runs/40771934419). All 143 tests, required detection validation and workflow lint passed; these local/mock checks are separate from the actual REST/Kusto evidence.
- [Source inventory](../ama/source.json), [onboarding and operation](onboarding/local-linux-ama.md), [complete validation and troubleshooting](validation/local-linux-ama.md). AMA remains outside the existing health evaluator until an explicit freshness/maintenance policy is implemented. This pilot does not add active Linux detections, prove production accuracy or complete the eight-phase mission. Earlier pending-approval and disconnected snapshots remain historical records.

## Previous increment: Detection portfolio before SOAR

- The operator requested developing and implementing more detections under the existing subscription and budget constraints. [Portfolio coverage and runbooks](detections/portfolio.md): ten additional fixed disabled definitions, AZ-DET-003 through AZ-DET-012, using existing AzureActivity. No new source is necessary for this increment.
- Eight management-event signals, one repeated-failure threshold and one ordered role-grant/diagnostic-change correlation. Purpose, original-event lineage, entity limitations, MITRE mapping uncertainty, legitimate matches and coverage gaps are documented individually.
- Fixed-contract validation, 60 synthetic controls and 130 passing unit tests. Preview-first administrative reuse of existing identity/trust/roles, ten exact rule-scoped assignments and manual-only main OIDC deployment with a complete portfolio approval fingerprint. No activation, incidents, queries or paid workload.
- [PR #10](https://github.com/miguelcastu/SentinelOps-MXDR/pull/10) merged as `4c12123` after required CI. Existing identity/trust/three roles reused; fourteen total exact assignments verified. The first run created eight rules then stopped at Azure's entity-mapping minimum. [Protected fix PR #11](https://github.com/miguelcastu/SentinelOps-MXDR/pull/11), merge `38f1627`, maps the aggregate to the actual resource-group context and adds the API regression guard; [required Python 3.12 CI](https://github.com/miguelcastu/SentinelOps-MXDR/actions/runs/39235750854) passed.
- [Successful main OIDC deployment](https://github.com/miguelcastu/SentinelOps-MXDR/actions/runs/39235924991) at 19 October 10:14:14 UTC verified the eight existing definitions without PUT and created the last two disabled. [Actual sanitized deployment](../evidence/detection-portfolio/deployment.sanitized.json), [independent preservation audit](../evidence/detection-portfolio/preservation.sanitized.json) and [validation record](validation/detection-portfolio.md). Thirteen total rules: twelve managed disabled plus existing Fusion enabled. Subscription/tenant pin, pricing/retention/cap and original rule properties preserved; zero new sources, paid components, log queries, incidents or activation. Fresh telemetry/runtime/accuracy and billing balance were not measured. Evidence delivery follows the protected PR path.

## Previous increment: Phase 4

- [Risk package](../rba/), versioned signal catalog, explicit fictional identity mapping, synthetic source adapters and [signal schema](../schemas/rba-signal.schema.json).
- AF-RBA-001: one account's ordered failed authentication -> success -> role grant -> diagnostic change -> endpoint execution; exact host/scope joins, bounded windows and deterministic original-event deduplication.
- Account risk with confidence weights, per-kind/global caps, half-life decay, contribution ledgers, history and narrow event-time maintenance exceptions.
- Default scenario: 18 envelopes / 16 unique events / two replays / three accounts; one High-priority synthetic finding with Low confidence. Nine positive/benign/edge scenario checks; interactive replay dashboard and investigation artifact.
- [Operations design](operations/risk-correlation.md), [validation record](validation/phase-4.md), offline CI step. 112 tests pass on Python 3.12/3.15; 95 independent JSON Schema cases, six workflow YAML files, actionlint and documentation links pass. [Synthetic dataset](../evidence/phase-4/dataset.synthetic.json) and [risk report](../evidence/phase-4/risk-report.synthetic.json) preserve the evidence chain and configuration hash. Existing Azure definitions, roles, subscription and resource settings are untouched. Delivery: [PR #9](https://github.com/miguelcastu/SentinelOps-MXDR/pull/9), implementation commit `d46f19b`; the [required offline CI](https://github.com/miguelcastu/SentinelOps-MXDR/actions/runs/39167931811) passed on that implementation. The PR records final-head CI and protected merge SHA. No Azure workflow was dispatched for this increment.

## Previous increment: Phase 3

- [Health package](../platform_health/), per-source policies, last-seen/latency/volume/quality metrics and cost completeness.
- Eleven deterministic, in-memory fault scenarios; no changes to collection.
- Standalone local HTML dashboard plus JSON/Markdown reports; explicit synthetic/external/cloud-configuration evidence labels.
- Manual `check-health.yml`: existing workspace/rule GETs, one bounded Actions history read, sanitized summary and nonzero exit on demonstrated configuration drift.
- [Operations runbook, thresholds and SLIs](operations/platform-health.md), [validation record](validation/phase-3.md), and offline CI coverage. Checks: 89 tests pass on Python 3.12/3.15, both detection validators, six YAML files, actionlint and documentation links pass.
- Actual [read-only OIDC run](https://github.com/miguelcastu/SentinelOps-MXDR/actions/runs/39153342114) succeeded after protected [PR #7](https://github.com/miguelcastu/SentinelOps-MXDR/pull/7), implementation `c784afa`, merge `d1503fc`. [PR CI](https://github.com/miguelcastu/SentinelOps-MXDR/actions/runs/39153235274) and [main CI](https://github.com/miguelcastu/SentinelOps-MXDR/actions/runs/39153309790) passed.
- [Sanitized cloud aggregate](../evidence/phase-3/health-report.sanitized.json) and [synthetic fault evidence](../evidence/phase-3/fault-injection.sanitized.json). Local reports: `.local/platform-health/` (synthetic) and `.local/platform-health-live/` (actual configuration audit). Evidence delivery: [protected PR #8](https://github.com/miguelcastu/SentinelOps-MXDR/pull/8), initial evidence commit `a5528da`; the PR records final-head CI and merge SHA.

## Previous increment: Phases 1 and 2

- [Detection audit and approval proposal](detections/lifecycle-validation.md), synthetic triage, benign-match examples and failed-attempt coverage gaps.
- [Ingestion package](../ingestion/), strict [source schema](../schemas/synthetic-auth.schema.json), deterministic events and UTC normalization.
- [Source inventory](../ingestion/sources.json), [onboarding template](onboarding/source-template.md) and [source runbook](onboarding/synthetic-authentication.md).
- [DCR/table REST bodies](../infrastructure/ingestion/), exact contract checks, bounded transport and aggregate [validation KQL](../ingestion/validation.kql).
- Offline CI validates both detections and the new synthetic pipeline without Azure credentials or OIDC permissions.
- [Baseline, billing, cost estimate and validation evidence](validation/phase-1-2.md).

## Verified Azure and cost state

The current 28 October Arc/AMA control-plane, RBAC and financial observations are linked above and in [validation](validation/local-linux-ama.md). The subscription and workspace controls match their private baseline. One explicitly approved ten-message batch reached Syslog; no second batch, continuous collection, active alert or zero-cost claim is implied. The powered-off local guest stops its own forwarding, while existing unrelated workloads may still incur charges. No Azure VM, paid add-on, pricing/retention/cap/budget/diagnostic change, subscription switch or upgrade was made.

Earlier 18-19 October detection, health and billing observations are historical and do not establish current source arrival or rule runtime. Platform-health overall telemetry/export/runtime remains Unknown; the new bounded Syslog proof does not refresh every source or measure false positives. Phase 4 remains fully synthetic/offline. The separate synthetic-authentication DCR/custom table is still not provisioned.

## Checks and GitHub delivery

Prior successful deployments: [001](https://github.com/miguelcastu/SentinelOps-MXDR/actions/runs/39134917660), [002](https://github.com/miguelcastu/SentinelOps-MXDR/actions/runs/39134917548). These are prior evidence, not new ingestion evidence.

Delivery: [PR #6](https://github.com/miguelcastu/SentinelOps-MXDR/pull/6), branch `feat/phase-two-bounded-ingestion`, implementation commit `613f11b`. The [required offline CI](https://github.com/miguelcastu/SentinelOps-MXDR/actions/runs/39142405359) passed on that implementation. Local verification: 67 tests pass on Python 3.12 and 3.15, both detection contracts pass, independent JSON Schema validation passes for 100 events, five workflow YAML files parse, actionlint and Markdown link checks pass. The PR records final-head checks and the protected merge SHA. No unchanged rule deployment is needed for this offline increment.
