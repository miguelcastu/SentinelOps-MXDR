# AZ-DET-001 — Azure Diagnostic Settings Modified

Status: implemented as code, **disabled**. Cloud deployment and real Kusto execution are pending prerequisite completion. Historical screenshots do not prove this rule exists or that this implementation has been deployed.

## Purpose and data source

Identify successful changes to Azure diagnostic settings that could interrupt security telemetry. Reads only the existing workspace's `AzureActivity` table. It does not create diagnostic settings, export activity, generate management events or ingest synthetic fixtures.

## Logic and schedule

[KQL source](../../detections/azure/AZ-DET-001.kql) and [REST body](../../detections/azure/AZ-DET-001.json) must contain exactly the same query. The restricted validator rejects additional operators, sources and unapproved fields.

- Case-insensitive exact operations: `Microsoft.Insights/diagnosticSettings/write` and `/delete`.
- Success statuses: `Success` and `Succeeded`; failures, start/accept events and substring matches do not qualify.
- Inclusive event-time window from `ago(1h)` through `now()`. Schedule: every 15 minutes, lookback: one hour.
- Medium severity; more than zero results would trigger an alert if separately approved and enabled.
- `distinct *` removes identical projected rows within each execution. It does not prevent overlapping-window matches across executions.
- Rule disabled, incident creation disabled, no playbook or automation resources.

Microsoft documents the [AzureActivity columns](https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/azureactivity), including the success-status variation. This rule is intentionally more conservative than matching any operation containing `diagnosticSettings`.

## MITRE ATT&CK and entities

REST mapping: `DefenseEvasion`, `T1562.008` (the historical Impair Defenses / Disable Cloud Logs mapping used by Sentinel content). The checked [Sentinel API schema](https://learn.microsoft.com/en-us/rest/api/securityinsights/alert-rules/create-or-update?view=rest-securityinsights-2025-09-01) still exposes `DefenseEvasion`. MITRE's current catalog [maps cloud-log impairment to T1685.002](https://attack.mitre.org/wiki/Technique/T1562/008/). Catalog migrations need a separately reviewed Sentinel compatibility check; this definition does not claim the historical ID is the latest MITRE catalog ID.

| Entity | Identifier | Output column | Handling |
|---|---|---|---|
| AzureResource | ResourceId | TargetResourceId | Prefer `ResourceId`, fall back to `_ResourceId` |
| IP | Address | SourceIPAddress | `parse_ipv6` accepts IPv4/IPv6; reject empty parses and CIDR networks |

The [Kusto IPv6 parser](https://learn.microsoft.com/en-us/kusto/query/parse-ipv6-function?view=microsoft-fabric) returns an empty string for invalid input, so the query uses `isnotempty`, rather than a null check. Its accepted CIDR input is explicitly excluded from IP entities. `Caller` remains a custom detail: it can represent different principal types and is not safely assumed to be a human UPN or Entra user object. Custom details also include operation, status, correlation and event ID. These alert details can contain sensitive telemetry if the rule is enabled later; CI never prints the query's event rows.

## False positives and investigation

Legitimate Azure Policy remediation, infrastructure automation, administrator changes, deployment pipelines and resource cleanup can match. A write does not prove logs were disabled: inspect the diagnostic destinations, enabled categories, change authorization and related activity privately. This first version has no allowlist.

## Tests and evidence

`python -m unittest discover -s tests -v` checks synthetic positive, negative, mixed-case, inclusive-boundary, stale/future and missing-identity cases. The offline interpreter exercises only the parsed filter contract; it is **not a Kusto runtime** and does not validate Azure's IP parsers or entity resolution.

The optional read-only workflow executes the actual query body over synthetic `datatable` input and checks event-ID set differences against expectations. It also runs a real-data aggregate. Fixtures never enter Log Analytics ingestion. See the [pipeline runbook](../deployment/detection-cicd.md) and [validation record](../validation/detection-cicd.md).

## Operational limitations

- An hour lookback every 15 minutes overlaps. The same event can appear in successive runs if enabled; cross-run deduplication is not implemented.
- Events arriving more than an hour after event time can be missed. This is not an ingestion-time cursor.
- Diagnostic changes that remove this workspace's own logging route may reduce subsequent visibility.
- Empty counts can be normal lab inactivity. Success does not establish malicious intent, complete source coverage or a production SLA.
- The Azure resource's existence, current state and exclusive deployment ownership must be confirmed before the first update.
- This workflow requires an already disabled rule; it will not disable an enabled production rule automatically.
