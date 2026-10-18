# SentinelOps MXDR project status

Last updated: 18 October 2026. Read this file first when resuming. Atlas Financial is a fictional customer. This increment advances the partially implemented Phase 1 and implements Phase 2 offline, as requested. The eight-phase mission remains incomplete.

| Phase | State | Acceptance evidence / blocker |
|---|---|---|
| 1. Detection engineering and incident lifecycle | Partially complete | Two actual disabled deployments, fresh Azure audit, synthetic triage and investigation test plan. Actual alert -> incident -> classification requires approval and narrow access. |
| 2. Advanced ingestion | Offline complete; live blocked by approval | Generator, schema, normalization, bounded HTTP client tested with mocks, inventory, REST bodies, validation KQL and runbook. No DCR/table deployment or upload. |
| 3. Platform health | Pending | Next independent phase: inventory-driven evaluator and safe fault injection. |
| 4. Risk-based correlation | Pending | No scoring engine claimed. |
| 5. SOAR | Pending | No automation/Logic App claimed. |
| 6. Infrastructure and advanced CI/CD | Partial baseline | Restricted OIDC detection CI/CD exists; REST bodies are not platform Bicep or verified infrastructure deployment. |
| 7. Customer operations | Pending | Initial source onboarding and fictional customer context only. |
| 8. Portfolio completion | Pending | No final release or full completion claim. |

## Delivered in this increment

- [Detection audit and approval proposal](detections/lifecycle-validation.md), synthetic triage, benign-match examples and failed-attempt coverage gaps.
- [Ingestion package](../ingestion/), strict [source schema](../schemas/synthetic-auth.schema.json), deterministic events and UTC normalization.
- [Source inventory](../ingestion/sources.json), [onboarding template](onboarding/source-template.md) and [source runbook](onboarding/synthetic-authentication.md).
- [DCR/table REST bodies](../infrastructure/ingestion/), exact contract checks, bounded transport and aggregate [validation KQL](../ingestion/validation.kql).
- Offline CI validates both detections and the new synthetic pipeline without Azure credentials or OIDC permissions.
- [Baseline, billing, cost estimate and validation evidence](validation/phase-1-2.md).

## Verified Azure and cost state

18 October read-only audit: pinned subscription/tenant unchanged; West Europe workspace, 30-day retention and 0.1 GB daily cap. Both rules disabled, unique and matching all managed properties. One existing subscription export, workspace/solution/identity inventory preserved. Fresh telemetry arrival was not queried.

Free subscription remains active; spending limit On. Credit API closed balance EUR 175.99436818021823 (USD 200), expiry 12 November 2026 18:00:16 UTC; billing delays remain possible. Introduced Azure resources, roles, ingestion runs, queries and recurring workloads: **none**. Existing usage can still accrue charges. No subscription switch or upgrade.

## Checks and GitHub delivery

Prior successful deployments: [001](https://github.com/miguelcastu/SentinelOps-MXDR/actions/runs/39134917660), [002](https://github.com/miguelcastu/SentinelOps-MXDR/actions/runs/39134917548). These are prior evidence, not new ingestion evidence.

Branch: `feat/phase-two-bounded-ingestion`. Local verification: 67 tests pass on Python 3.12 and 3.15, both detection contracts pass, independent JSON Schema validation passes for 100 events, five workflow YAML files parse, actionlint and Markdown link checks pass. Commit, PR and CI references will be recorded after remote verification. Use protected PR checks/merge; do not redeploy unchanged rules solely to produce activity.

## Next executable task

Without new Azure access or spend: Phase 3 source-health evaluation and local fault scenarios from the source inventory, after the operator requests the next phase. Quiet event-driven AzureActivity must not be classified as Missing solely because one window has no events.

For live acceptance: approve the concrete [Phase 1 test](detections/lifecycle-validation.md) or [Phase 2 cloud design](onboarding/synthetic-authentication.md), then implement/review the gated workflows and narrow OIDC roles, recheck finances and execute only the approved bounded test. Existing detection deployment roles remain unchanged. Current authorization does not permit those cloud expansions.
