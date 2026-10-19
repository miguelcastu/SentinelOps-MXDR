# AZ-DET-012 - Role Grant Followed by Diagnostic Change

Purpose: Successful role assignment followed strictly within fifteen minutes by a diagnostic setting write/delete by the same caller in the same subscription/resource group. Resource-group correlation does not prove equal RBAC/diagnostic target scope or causal privilege use.

| Property | Contract |
|---|---|
| Source | Existing AzureActivity, management plane |
| Fixed resource UUID | `eed467bf-df6d-5fa9-8957-6c916e680bcc` |
| Priority | High; rule priority is not an attack verdict |
| State | Disabled; incident creation false; no automation |
| Schedule / lookback | PT15M / PT1H; bounded inclusive event-time filter |
| MITRE in REST | T1098, T1562 |
| Entity handling | AzureResource (TargetResourceId) and a valid optional IP (SourceIPAddress) |

[KQL](../../detections/azure/AZ-DET-012.kql) and [REST body](../../detections/azure/AZ-DET-012.json) are bound to the reviewed fixed contract. Only exact case-insensitive operation names and terminal statuses match. The operation identifiers are:

- `Microsoft.Authorization/roleAssignments/write`
- `Microsoft.Insights/diagnosticSettings/write`
- `Microsoft.Insights/diagnosticSettings/delete`

Original EventDataId is mandatory; per-run deduplication selects the latest row for each source ID. Empty original IDs are omitted and must be counted during a separately authorized live quality assessment. Caller is kept as context because its GUID/UPN/application meaning is not established by this query. IPv4/IPv6 values are mapped only when valid and not CIDR ranges; keys, claims, request bodies and secret values are never projected. AZ-DET-011 deliberately has no IP mapping after aggregation.

False positives: An approved CI deployment can legitimately grant access and update diagnostics in the same subscription/resource group. There is no unconditional CI/administrator allowlist. Proposed exceptions must bind actor, exact scope, operation, change authorization and expiry, with regression cases. No real-data precision or false-positive rate has been measured.

Investigation: Review both original event IDs, role principal/definition/scope, diagnostic delta, caller and approved deployment. Establish causality before escalation. Use authorized private evidence; do not block an account, remove permissions or delete resources automatically.

Limitations: Subscription, caller and resource-group equality are context joins, not equal target scope or proof that the assigned principal is the caller. Empty subscription/caller/group/ID is excluded; subscription-scoped role grants may be missed. Latest preceding grant is selected, with a stable event-ID tie-break. These rules share overlapping one-hour lookbacks and fifteen-minute schedules. Per-run deduplication does not suppress repeats across executions; incident grouping is disabled. There is no lateness guarantee or proof of fresh telemetry. Broad single-event rules are deliberately lower-priority candidates for investigation.

Testing: `python -m portfolio` exercises explicit positive, replay, started, wrong-operation, stale and missing-lineage controls. `tests/test_portfolio.py` adds thresholds, identity/scope separation, boundary/order/tie handling and deployment fault cases. The Python reference model is not Kusto execution or live detection validation. The [portfolio validation record](../validation/detection-portfolio.md) tracks deployment evidence separately.

See [portfolio coverage, taxonomy and source references](portfolio.md). Deployment neither provisions the monitored resource nor establishes its presence in this subscription.
