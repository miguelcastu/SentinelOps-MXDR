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

KQL templates and the response adapter have been reviewed and tested structurally/offline. **The queries have not been executed in Kusto.** Local p95 is nearest-rank and KQL uses its documented percentile implementation; no equivalence/performance claim is made.

## Cloud verification checkpoint

The manual `Read-only Platform Health` workflow must first be merged through the protected PR path, then executed once on main. It reuses existing OIDC/RBAC and performs only existing workspace/rule GETs plus a bounded GitHub Actions history read. Cloud execution evidence and final CI references will be recorded after that run. No live telemetry, new query permissions, connector changes or billing feature is authorized by this workflow.

Expected honest limitations: source telemetry Unknown, export configuration Unknown under CI permissions, rule execution Unknown, and no verified invoice. The two disabled managed rule definitions should match their persisted configuration. Existing Fusion remains outside the managed rule counters and is not modified.

## Cost and preservation

No new Azure resources, role assignments, ingestion, scheduled queries, SentinelHealth export or recurring automation are introduced. The manual check uses existing metadata permissions. Local demos execute zero network calls. Standard public GitHub runners and summaries are used without artifact uploads. Credit/expiry evidence in the previous checkpoint remains historical; this phase does not claim a refreshed credit balance or zero total subscription charges.

Read the [runbook and threshold rationale](../operations/platform-health.md) and [project checkpoint](../PROJECT_STATUS.md) for acceptance and next steps.
