# AZ-DET-008 - Resource Lock Removed

Purpose: Successful resource lock deletion. Check authorization and subsequent writes/deletions; this does not prove destruction.

| Property | Contract |
|---|---|
| Source | Existing AzureActivity, management plane |
| Fixed resource UUID | `11169c66-cfdb-5b40-94ec-4d01c3845503` |
| Priority | Low; rule priority is not an attack verdict |
| State | Disabled; incident creation false; no automation |
| Schedule / lookback | PT15M / PT1H; bounded inclusive event-time filter |
| MITRE in REST | Unmapped: this management event alone does not support a precise technique claim |
| Entity handling | AzureResource (TargetResourceId) and a valid optional IP (SourceIPAddress) |

[KQL](../../detections/azure/AZ-DET-008.kql) and [REST body](../../detections/azure/AZ-DET-008.json) are bound to the reviewed fixed contract. Only exact case-insensitive operation names and terminal statuses match. The operation identifiers are:

- `Microsoft.Authorization/locks/delete`

Original EventDataId is mandatory; per-run deduplication selects the latest row for each source ID. Empty original IDs are omitted and must be counted during a separately authorized live quality assessment. Caller is kept as context because its GUID/UPN/application meaning is not established by this query. IPv4/IPv6 values are mapped only when valid and not CIDR ranges; keys, claims, request bodies and secret values are never projected. AZ-DET-011 deliberately has no IP mapping after aggregation.

False positives: Approved infrastructure retirement, maintenance or lock replacement. There is no unconditional CI/administrator allowlist. Proposed exceptions must bind actor, exact scope, operation, change authorization and expiry, with regression cases. No real-data precision or false-positive rate has been measured.

Investigation: Check lock type and affected scope, approval, replacement guardrails and subsequent destructive operations. Use authorized private evidence; do not block an account, remove permissions or delete resources automatically.

Limitations: No destructive operation is inferred and no response action is automated. A removed lock can have no security significance. These rules share overlapping one-hour lookbacks and fifteen-minute schedules. Per-run deduplication does not suppress repeats across executions; incident grouping is disabled. There is no lateness guarantee or proof of fresh telemetry. Broad single-event rules are deliberately lower-priority candidates for investigation.

Testing: `python -m portfolio` exercises explicit positive, replay, started, wrong-operation, stale and missing-lineage controls. `tests/test_portfolio.py` adds thresholds, identity/scope separation, boundary/order/tie handling and deployment fault cases. The Python reference model is not Kusto execution or live detection validation. The [portfolio validation record](../validation/detection-portfolio.md) tracks deployment evidence separately.

See [portfolio coverage, taxonomy and source references](portfolio.md). Deployment neither provisions the monitored resource nor establishes its presence in this subscription.
