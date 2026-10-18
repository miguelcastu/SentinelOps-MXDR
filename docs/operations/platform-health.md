# Phase 3: platform health and observability

This implementation evaluates the fictional Atlas Financial lab using the existing [source inventory](../../ingestion/sources.json). It provides deterministic local fault injection, aggregate-data validation, a standalone coverage dashboard and an opt-in **read-only** OIDC configuration check. It does not provision an Azure monitoring service, enable Sentinel health logging, run log queries, start a schedule or change ingestion.

## Run locally

```powershell
python -m platform_health
python -m unittest discover -s tests -v
```

Open `.local/platform-health/dashboard.html` in a browser. The self-contained report has a source-state filter and no external assets or network requests. JSON and Markdown reports are written beside it. **Default evidence is labeled synthetic** and evaluated at a fixed demonstration time; a green demo is not evidence that Azure ingestion is healthy today.

To evaluate a bounded external aggregate snapshot:

```powershell
python -m platform_health --snapshot .local/approved-health-snapshot.json
```

The input limit is 128 KiB. Imported data is always relabeled `external-aggregate`, even if it claims to be Azure-verified. Evaluation uses current UTC time unless `--as-of` supplies an explicit historical timestamp. Snapshot contracts reject raw fields, unrecognized sources/checks, invalid counts, unbounded windows, ambiguous timestamps and contradictory totals. The CLI prints only the normalized, allowlisted report; it does not echo a failed input or an Azure exception.

Input snapshots follow the observation contract in `engine.py`; generated `report.json` files are output reports, not input snapshots. To create a labeled example and re-evaluate its historical window:

```powershell
python -c "import json; from pathlib import Path; from platform_health.demo import baseline; Path('.local/health-snapshot.json').write_text(json.dumps(baseline()), encoding='utf-8')"
python -m platform_health --snapshot .local/health-snapshot.json --as-of 2026-10-18T12:00:00Z --output .local/health-import-example
```

## Collection and evidence boundaries

| Area | Implemented measurement | Actual access boundary |
|---|---|---|
| Source ownership/onboarding | Inventory, table, owner, collection model and onboarding state | Local inventory; one previously onboarded AzureActivity source, one offline-only synthetic source |
| Freshness and last seen | Last event and observation timestamps; stale data becomes Unknown | Synthetic/external aggregates; no live telemetry query access granted |
| Volume | Bounded hourly counts; zero-event handling without invented heartbeat | Demo buckets and KQL template; missing buckets are not silently filled by Python |
| Latency | p95, negative-latency counter, per-source warning thresholds | Offline nearest-rank p95; KQL percentile estimates remain unexecuted |
| Schema and parsing | Required-field/type errors, normalization mapping errors and schema evolution | Fault injection mutates normalized events and derives error counts |
| Duplicates | Exact original-event ID counts and uniqueness ratio | Duplicate rows are quality findings; no exactly-once ingestion promise |
| Rule configuration | Full managed-property comparison for AZ-DET-001 and AZ-DET-002 | Existing workspace alertRules/read permission |
| Rule execution | Separate Unknown component | SentinelHealth was not enabled or queried; disabled rules are not active coverage |
| Workspace configuration | Region, pricing tier, retention and daily cap drift | Existing workspace metadata read permission; case-normalized SKU comparison |
| Connector/export configuration | Unknown component with an explicit reason | CI cannot read subscription diagnostic settings; no silent RBAC expansion |
| Deployment failures | Latest observed run per approved workflow | One bounded GitHub Actions read request; no raw author/commit identities retained |
| Cost awareness | Observed billable bytes, known-source count and partial planning estimate | Not an invoice, credit balance or forecast for unobserved sources |

Managed rule counts exclude Fusion and any unmanaged rules. The expected two rules remain intentionally disabled. `matching=2, active=0` means the reviewed configurations match, not that the platform has no other active analytics.

## Classification and thresholds

The [policies](../../platform_health/policies.json) are operational demonstration thresholds, **not customer SLAs**. AzureActivity is event-driven; the synthetic source has only explicitly approved test batches. Neither has a periodic heartbeat requirement. A new continuous source must define its own heartbeat policy before Missing alarms are appropriate.

| State | Decision |
|---|---|
| Healthy | Fresh complete evidence, valid unique events, sufficient latency/freshness metrics, and a satisfied explicit batch expectation if provided |
| Delayed | p95 above 900 seconds for AzureActivity or 300 seconds for synthetic authentication |
| Missing | An explicitly expected synthetic batch has fewer unique events than expected after its stated deadline |
| Misconfigured | Demonstrated schema/mapping/clock/duplicate problem, configuration drift or failed latest deployment |
| Unknown | Quiet event-driven source, no active batch, absent/partial/unauthorized query, stale observation or incomplete metrics |

Observations older than 900 seconds are stale. Events last seen more than one hour ago give insufficient freshness evidence; without a heartbeat they do not prove an outage. A 60-second clock tolerance prevents small observation skew from becoming a false alarm. Negative event-to-ingestion latency is still a clock-quality fault. Pending batch deadlines may be at most 15 minutes beyond the observation window. One observed malformed/mis-mapped/duplicate event flags Misconfigured in this small lab; a production threshold needs a baseline and a change review.

Known faults take precedence over missing data: Misconfigured -> Missing -> Delayed -> Unknown -> Healthy. Overall state can therefore be Unknown when configuration checks pass but ingestion was not measured. A source row and a configuration row answer different questions.

## Metrics and SLIs

- Source observation coverage = queried sources / inventoried sources. Cloud onboarding coverage comes from inventory and is distinct from current health.
- Schema validity = valid events / total; uniqueness = distinct original IDs / total. Ratios are null when no events exist, rather than a misleading 100%.
- Ingestion latency = `ingestion_time() - TimeGenerated`; it includes source/transport delays and clock error. It is not pure Azure processing time. See [Microsoft ingestion-time guidance](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/data-ingestion-time).
- Window volume counts come only from supplied aggregates; [24-hour KQL](../../platform_health/queries/activity-volume.kql) produces exactly 24 completed hourly bins, including zeros using `kind=nonempty`.
- Deployment health uses the latest observed run of each of three known workflows, never an older failure after a later success. Running/cancelled/skipped/missing runs are Unknown. One API page of 30 main-branch runs can omit older workflows; that limitation remains visible as Unknown.
- Configuration agreement measures all approved rule properties, not just enabled state. Unexpected enabled state or duplicate rule name is drift.

These are point-in-time operational metrics. No uptime percentage, historical availability SLO, completeness for unobserved sources or production false-positive rate is claimed.

## Manual Azure/GitHub verification

Run **Read-only Platform Health** (`check-health.yml`) on main. The current phase authorizes this read-only check using the existing main-only environment, identity and permissions. It performs only two Azure resource GETs: existing workspace metadata and existing analytics-rule inventory. Azure CLI also verifies the current service-principal account. It makes one GitHub workflow-history request, shares the deployment concurrency group to avoid reading mid-deployment, and has a six-minute timeout. It never switches the subscription, falls back to a personal account, modifies a resource or adds a role.

The job writes a sanitized step summary and JSON report to the workflow log, without uploading artifacts. Configuration drift produces exit code 2 **after** the report is written. Unknown data is reported honestly; a successful job means the read-only audit completed, not that all platform components are Healthy. Metadata access failures remain Unknown, and authentication/target/contract failures stop with a sanitized nonzero error.

New KQL files are [here](../../platform_health/queries/). The strict [aggregate adapter](../../platform_health/logs.py) accepts only one result row with known columns and rejects partial/error/raw-identity responses. It is offline tooling, not a query executor. Real KQL, schema queries, cost queries, runtime health and connector export reads still require separately approved access. Do not enable SentinelHealth/diagnostic export merely to make a dashboard green; additional collection can introduce costs. See Microsoft's [health-monitoring setup](https://learn.microsoft.com/en-us/azure/sentinel/enable-monitoring).

The Usage template filters one day and two known table types. [Usage.Quantity is MBytes](https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/usage); unexpected units are counted, and decimal GB conversion is explicit. Health queries sum only rows with `_IsBillable=true`; nonbillable AzureActivity storage bytes are not treated as paid ingestion. The EUR 10/GB planning rate is inherited from Phase 2 and is not a fresh price quote. Missing data means the cost estimate is incomplete, not zero. No billing API permission was granted to CI.

## Fault injection and troubleshooting

The [demo](../../platform_health/demo.py) runs eleven scenarios: healthy batch, missing approved batch, quiet activity, delayed events, malformed field type, wrong field mapping, schema evolution, duplicate event, configuration drift, failed deployment and partial query. Input mutations occur in memory and do not disable the active export. Tests additionally cover stale observations/last-seen, negative latency, clock skew, future acceptance deadlines, unauthorized queries and wrong-target guards.

| Finding | Repeatable investigation |
|---|---|
| Quiet AzureActivity / Unknown | Check observation window and source activity expectations; verify a pre-approved known event before alleging collection failure |
| Missing approved batch | Reconcile the private manifest, expected unique IDs, deadline and API receipts before replay |
| Delayed | Compare source clock, event time, transport receipt and ingestion time; inspect p95 and a bounded later observation |
| Schema/mapping error | Compare the versioned contract and DCR/table types; run only an authorized schema query; fix offline fixtures first |
| Duplicates | Reconcile retries and original IDs; avoid blind resends and downstream risk inflation |
| Rule/workspace drift | Inspect approved source vs actual GET privately; use the normal reviewed deployment path for any correction |
| Failed deployment | Inspect the latest relevant workflow, required environment and OIDC context; never bypass protections or broaden roles |
| Export Unknown | Existing CI lacks that read permission; retain earlier export evidence as historical, and request narrow access only if live validation is needed |
| Partial cost estimate | Collect approved billable usage aggregates and verify the effective pricing plan; never assume a daily cap is a financial hard stop |

Stopping this tooling requires no cloud rollback: it is one-shot and read-only. Remove local reports if desired; no Azure resource, query schedule, health alert or ingestion setting was created.
