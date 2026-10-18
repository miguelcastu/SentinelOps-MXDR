# Phase 3 validation: platform health

## Implemented offline

The new health package uses the existing source inventory and per-source policies. Default evidence is explicitly synthetic. The demo runs eleven scenarios from mutated in-memory events or configuration/workflow fixtures and checks each expected classification. Reports contain only allowlisted aggregate metrics and public source/check names.

```powershell
python -m platform_health
python -m unittest discover -s tests -v
python -m scripts.validate_detection
```

The local dashboard is `.local/platform-health/dashboard.html`; JSON/Markdown are alongside it. It is a standalone artifact with no server, external assets, tracking or browser network requests. It separates source onboarding/health, managed rule configuration/active coverage, cost completeness and fault examples.

Validation covers quiet AzureActivity without false Missing alarms, expected-batch deadlines, stale snapshots, source-specific latency thresholds, unknown query results, schema/mapping failures, duplicates, negative latency, clock skew, wrong target guards, bounded resource reads, duplicate/enabled/missing/drifted rules, incomplete inventories, latest deployment status, privacy and static report escaping. Existing ingestion and detection tests remain part of the same suite.

Local verification: **89 tests pass on Python 3.12 and Python 3.15**. Both disabled detection contracts pass, all six workflow YAML files parse, actionlint passes and documentation file links resolve. Staged whitespace and private-target/credential scans are required before committing. No third-party runtime package was added.

KQL templates were manually reviewed; the aggregate-response adapter was tested offline. **The queries have not been executed or parsed by Kusto.** Local p95 is nearest-rank and KQL uses its documented percentile implementation; no equivalence/performance claim is made.

## Actual OIDC cloud verification

Implementation was merged through protected [PR #7](https://github.com/miguelcastu/SentinelOps-MXDR/pull/7), commit `c784afa`, merge `d1503fc`. The [required PR CI](https://github.com/miguelcastu/SentinelOps-MXDR/actions/runs/39153235274) and [main CI](https://github.com/miguelcastu/SentinelOps-MXDR/actions/runs/39153309790) passed.

The manual [Read-only Platform Health run](https://github.com/miguelcastu/SentinelOps-MXDR/actions/runs/39153342114) was dispatched **once**, on main after CI passed, and completed successfully using the existing OIDC identity/permissions. Observation timestamp: **18 October 2026, 18:15:54 UTC**. It performed only two Azure metadata GETs and one bounded GitHub Actions history request; it executed no KQL, mutation or subscription switch.

Actual [sanitized aggregate evidence](../../evidence/phase-3/health-report.sanitized.json) records:

| Check | Actual result |
|---|---|
| Workspace region/pricing tier/retention/cap | Healthy: matches West Europe, PerGB2018, 30 days and 0.1 GB |
| AZ-DET-001 managed configuration | Healthy: every approved property matches; intentionally disabled |
| AZ-DET-002 managed configuration | Healthy: every approved property matches; intentionally disabled |
| Latest observed validation and two deployment workflows | Healthy: successful runs |
| Source telemetry | Unknown: zero sources queried; no zero-event or outage inference |
| Export configuration | Unknown: existing CI lacks subscription-export read access |
| Rule execution | Unknown: runtime health was not collected |
| Cost evidence | Incomplete: no billable usage observed, no invoice verification |

Overall platform state is **Unknown**, correctly reflecting unmeasured components rather than pretending complete platform health. The successful workflow means this bounded audit completed. Managed rule counts are two matching, zero active and two intentionally disabled; Fusion remains outside these counters and was not modified.

The sanitized report was recovered from the job log, verified against the successful run/head SHA and checked for private target identifiers. A live local dashboard is saved under `.local/platform-health-live/dashboard.html`. No artifact upload or paid storage was used. The [eleven synthetic fault outcomes](../../evidence/phase-3/fault-injection.sanitized.json) remain separately labeled and are not cloud failure evidence.

Phase 3's acceptance criterion is met: repeatable simulations identify/explain collection-quality failures, and actual configuration/deployment observations are verified through the approved read-only path. Live ingestion, connector/export drift and rule-runtime health require additional evidence/access and remain explicitly unverified. No alert or health resource was enabled to fill those gaps.

## Cost and preservation

No new Azure resources, role assignments, ingestion, scheduled queries, SentinelHealth export or recurring automation are introduced. The manual check uses existing metadata permissions. Local demos execute zero network calls. Standard public GitHub runners and summaries are used without artifact uploads. Credit/expiry evidence in the previous checkpoint remains historical; this phase does not claim a refreshed credit balance or zero total subscription charges.

Read the [runbook and threshold rationale](../operations/platform-health.md) and [project checkpoint](../PROJECT_STATUS.md) for acceptance and next steps.
