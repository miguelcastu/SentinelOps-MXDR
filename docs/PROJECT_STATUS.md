# SentinelOps MXDR project status

Last updated: 28 October 2026. Read this file first when resuming. Atlas Financial is a fictional customer. Current increment: personally owned local Linux VM and one explicitly approved Arc/AMA pilot. The bounded Arc/AMA pilot is verified end to end and the local guest is stopped. The eight-phase mission remains incomplete.

| Phase | State | Acceptance evidence / blocker |
|---|---|---|
| 1. Detection engineering and incident lifecycle | Portfolio deployed; live lifecycle pending | Twelve actual disabled definitions, fresh REST verification, per-rule investigations, synthetic controls and test plan. Actual alert -> incident -> classification requires approval and narrow access. |
| 2. Advanced ingestion | Synthetic offline complete; owned Linux AMA pilot verified | Actual Arc/AMA/DCR configuration, main OIDC verification and ten unique Syslog messages reconciled. Local guest stopped; separate synthetic-auth custom-table deployment and continuous health remain pending. |
| 3. Platform health | Implemented and verified within current scope | Eleven simulated faults and actual read-only OIDC configuration/deployment audit verified. Live telemetry/export/runtime remain Unknown; no query access or health export added. |
| 4. Risk-based correlation | Implemented and verified offline | Bounded entity scoring, strict multi-stage sequence, decay/caps/deduplication, narrow maintenance context, health-aware confidence and replay report. No Sentinel incident or live validation. |
| 5. SOAR | Pending | No automation/Logic App claimed. |
| 6. Infrastructure and advanced CI/CD | Partial baseline | Restricted OIDC detection CI/CD exists; REST bodies are not platform Bicep or verified infrastructure deployment. |
| 7. Customer operations | Pending | Initial source onboarding and fictional customer context only. |
| 8. Portfolio completion | Pending | No final release or full completion claim. |

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

## Next executable task

The approved local-machine increment is complete. Keep the guest stopped and retain both completed private ledgers. Do not reconnect Arc, rerun personal initialization, replay the ten-message batch or use the unused third query without a reason and appropriate authorization. The same DCR would collect qualifying local4 messages again if the guest were started.

When requested, develop Linux detection candidates and AMA health policies **offline**, explaining which additional facilities/severities would be needed; the current local4 test data does not support native SSH detection. New collection, another pilot, real-data false-positive assessment, rule activation or incidents need their own concrete approved scope. The twelve AzureActivity definitions remain disabled.

Phase 5 remains **offline SOAR and case management** when requested, using synthetic RBA findings, idempotent intake, entity enrichment, investigation notes, safe approval gates, audit logging and bounded retries. Do not create Logic Apps, paid SaaS, real incidents or containment actions without separate authorization. The separate Phase 1 live lifecycle test and synthetic-authentication custom-table cloud path remain unapproved.
