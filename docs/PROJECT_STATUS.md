# SentinelOps MXDR project status

Last updated: 18 October 2026. Read this file first when resuming. Atlas Financial is a fictional customer. Current increment: Phase 4 offline risk correlation. The eight-phase mission remains incomplete.

| Phase | State | Acceptance evidence / blocker |
|---|---|---|
| 1. Detection engineering and incident lifecycle | Partially complete | Two actual disabled deployments, fresh Azure audit, synthetic triage and investigation test plan. Actual alert -> incident -> classification requires approval and narrow access. |
| 2. Advanced ingestion | Offline complete; live blocked by approval | Generator, schema, normalization, bounded HTTP client tested with mocks, inventory, REST bodies, validation KQL and runbook. No DCR/table deployment or upload. |
| 3. Platform health | Implemented and verified within current scope | Eleven simulated faults and actual read-only OIDC configuration/deployment audit verified. Live telemetry/export/runtime remain Unknown; no query access or health export added. |
| 4. Risk-based correlation | Implemented and verified offline | Bounded entity scoring, strict multi-stage sequence, decay/caps/deduplication, narrow maintenance context, health-aware confidence and replay report. No Sentinel incident or live validation. |
| 5. SOAR | Pending | No automation/Logic App claimed. |
| 6. Infrastructure and advanced CI/CD | Partial baseline | Restricted OIDC detection CI/CD exists; REST bodies are not platform Bicep or verified infrastructure deployment. |
| 7. Customer operations | Pending | Initial source onboarding and fictional customer context only. |
| 8. Portfolio completion | Pending | No final release or full completion claim. |

## Current increment: Phase 4

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

Phase 4 is completely offline: zero network calls in the risk engine/demo, no Azure queries or changes, no new paid resources, connectors, identities, role assignments, schedules or incidents. Existing subscription protections remain unchanged by this work. Azure and billing statements below are historical checkpoints; this increment did not refresh them or claim a live attack/incident.

Phase 3 at 18 October 2026 18:15:54 UTC: same expected workspace region/pricing/cap/retention and both managed rules match source. Latest observed validation/deployment runs succeeded. Source telemetry, export and rule-runtime are Unknown, so overall health is Unknown. Zero KQL requests or resource/role/billing/ingestion changes; existing identity and permissions were reused. No recurring workload. This did not refresh credit balance/expiry or prove current AzureActivity arrival.

18 October read-only audit: pinned subscription/tenant unchanged; West Europe workspace, 30-day retention and 0.1 GB daily cap. Both rules disabled, unique and matching all managed properties. One existing subscription export, workspace/solution/identity inventory preserved. Fresh telemetry arrival was not queried.

Free subscription remains active; spending limit On. Credit API closed balance EUR 175.99436818021823 (USD 200), expiry 12 November 2026 18:00:16 UTC; billing delays remain possible. Introduced Azure resources, roles, ingestion runs, queries and recurring workloads: **none**. Existing usage can still accrue charges. No subscription switch or upgrade.

## Checks and GitHub delivery

Prior successful deployments: [001](https://github.com/miguelcastu/SentinelOps-MXDR/actions/runs/39134917660), [002](https://github.com/miguelcastu/SentinelOps-MXDR/actions/runs/39134917548). These are prior evidence, not new ingestion evidence.

Delivery: [PR #6](https://github.com/miguelcastu/SentinelOps-MXDR/pull/6), branch `feat/phase-two-bounded-ingestion`, implementation commit `613f11b`. The [required offline CI](https://github.com/miguelcastu/SentinelOps-MXDR/actions/runs/39142405359) passed on that implementation. Local verification: 67 tests pass on Python 3.12 and 3.15, both detection contracts pass, independent JSON Schema validation passes for 100 events, five workflow YAML files parse, actionlint and Markdown link checks pass. The PR records final-head checks and the protected merge SHA. No unchanged rule deployment is needed for this offline increment.

## Next executable task

Phase 4 is implemented and verified offline, with delivery through protected PR #9. The next independent phase when requested is **Phase 5: offline SOAR and case management**, using synthetic RBA findings, idempotent intake, entity enrichment, investigation notes, safe approval gates, audit logging and bounded retries. Do not create Logic Apps, paid SaaS, real incidents or containment actions without separate authorization.

For live acceptance: approve the concrete [Phase 1 test](detections/lifecycle-validation.md) or [Phase 2 cloud design](onboarding/synthetic-authentication.md), then implement/review the gated workflows and narrow OIDC roles, recheck finances and execute only the approved bounded test. Existing detection deployment roles remain unchanged. Current authorization does not permit those cloud expansions.
