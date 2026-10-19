# AZ-DET-007 - Storage Account Keys Listed

Purpose: Successful storage account key-list action. Ordinary portal/automation also matches; no key material is queried or included.

| Property | Contract |
|---|---|
| Source | Existing AzureActivity, management plane |
| Fixed resource UUID | `4045d337-3c91-50c6-9a6d-cb434cd985d6` |
| Priority | Low; rule priority is not an attack verdict |
| State | Disabled; incident creation false; no automation |
| Schedule / lookback | PT15M / PT1H; bounded inclusive event-time filter |
| MITRE in REST | Unmapped: this management event alone does not support a precise technique claim |
| Entity handling | AzureResource (TargetResourceId) and a valid optional IP (SourceIPAddress) |

[KQL](../../detections/azure/AZ-DET-007.kql) and [REST body](../../detections/azure/AZ-DET-007.json) are bound to the reviewed fixed contract. Only exact case-insensitive operation names and terminal statuses match. The operation identifiers are:

- `Microsoft.Storage/storageAccounts/listKeys/action`

Original EventDataId is mandatory; per-run deduplication selects the latest row for each source ID. Empty original IDs are omitted and must be counted during a separately authorized live quality assessment. Caller is kept as context because its GUID/UPN/application meaning is not established by this query. IPv4/IPv6 values are mapped only when valid and not CIDR ranges; keys, claims, request bodies and secret values are never projected. AZ-DET-011 deliberately has no IP mapping after aggregation.

False positives: Portal browsing, approved deployment tooling and key-based application configuration. There is no unconditional CI/administrator allowlist. Proposed exceptions must bind actor, exact scope, operation, change authorization and expiry, with regression cases. No real-data precision or false-positive rate has been measured.

Investigation: Check which application/operator requested keys, the change approval and downstream access. Never paste keys into case notes. Use authorized private evidence; do not block an account, remove permissions or delete resources automatically.

Limitations: This observes the list action, not the returned keys, actual storage data access or exfiltration. Local roleAssignment/Key Vault evidence is separate. These rules share overlapping one-hour lookbacks and fifteen-minute schedules. Per-run deduplication does not suppress repeats across executions; incident grouping is disabled. There is no lateness guarantee or proof of fresh telemetry. Broad single-event rules are deliberately lower-priority candidates for investigation.

Testing: `python -m portfolio` exercises explicit positive, replay, started, wrong-operation, stale and missing-lineage controls. `tests/test_portfolio.py` adds thresholds, identity/scope separation, boundary/order/tie handling and deployment fault cases. The Python reference model is not Kusto execution or live detection validation. The [portfolio validation record](../validation/detection-portfolio.md) tracks deployment evidence separately.

See [portfolio coverage, taxonomy and source references](portfolio.md). Deployment neither provisions the monitored resource nor establishes its presence in this subscription.
