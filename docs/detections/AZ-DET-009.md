# AZ-DET-009 - Activity Log Alert Deleted

Purpose: Successful Activity Log alert deletion. Check ownership and replacement monitoring; deletion does not stop Activity Log collection.

| Property | Contract |
|---|---|
| Source | Existing AzureActivity, management plane |
| Fixed resource UUID | `765a60b1-d0e9-5cac-9baf-c790fd2e80cf` |
| Priority | Medium; rule priority is not an attack verdict |
| State | Disabled; incident creation false; no automation |
| Schedule / lookback | PT15M / PT1H; bounded inclusive event-time filter |
| MITRE in REST | T1562 |
| Entity handling | AzureResource (TargetResourceId) and a valid optional IP (SourceIPAddress) |

[KQL](../../detections/azure/AZ-DET-009.kql) and [REST body](../../detections/azure/AZ-DET-009.json) are bound to the reviewed fixed contract. Only exact case-insensitive operation names and terminal statuses match. The operation identifiers are:

- `Microsoft.Insights/activityLogAlerts/delete`

Original EventDataId is mandatory; per-run deduplication selects the latest row for each source ID. Empty original IDs are omitted and must be counted during a separately authorized live quality assessment. Caller is kept as context because its GUID/UPN/application meaning is not established by this query. IPv4/IPv6 values are mapped only when valid and not CIDR ranges; keys, claims, request bodies and secret values are never projected. AZ-DET-011 deliberately has no IP mapping after aggregation.

False positives: Approved alert migration, cleanup and decommissioning. There is no unconditional CI/administrator allowlist. Proposed exceptions must bind actor, exact scope, operation, change authorization and expiry, with regression cases. No real-data precision or false-positive rate has been measured.

Investigation: Check the deleted alert condition, action groups, owner, replacement detection and changes around the same time. Use authorized private evidence; do not block an account, remove permissions or delete resources automatically.

Limitations: Activity Log alerts differ from Sentinel analytics rules; deletion does not disable AzureActivity collection. Legacy Sentinel ATT&CK taxonomy is retained for API compatibility. These rules share overlapping one-hour lookbacks and fifteen-minute schedules. Per-run deduplication does not suppress repeats across executions; incident grouping is disabled. There is no lateness guarantee or proof of fresh telemetry. Broad single-event rules are deliberately lower-priority candidates for investigation.

Testing: `python -m portfolio` exercises explicit positive, replay, started, wrong-operation, stale and missing-lineage controls. `tests/test_portfolio.py` adds thresholds, identity/scope separation, boundary/order/tie handling and deployment fault cases. The Python reference model is not Kusto execution or live detection validation. The [portfolio validation record](../validation/detection-portfolio.md) tracks deployment evidence separately.

See [portfolio coverage, taxonomy and source references](portfolio.md). Deployment neither provisions the monitored resource nor establishes its presence in this subscription.
