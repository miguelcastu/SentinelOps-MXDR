# AZ-DET-010 - Policy Assignment Deleted

Purpose: Successful Azure Policy assignment deletion. Inspect the removed policy and exemptions; the assignment may be unrelated to security.

| Property | Contract |
|---|---|
| Source | Existing AzureActivity, management plane |
| Fixed resource UUID | `5eee8a54-76d0-53a6-8262-29b34d3bd7b9` |
| Priority | Low; rule priority is not an attack verdict |
| State | Disabled; incident creation false; no automation |
| Schedule / lookback | PT15M / PT1H; bounded inclusive event-time filter |
| MITRE in REST | Unmapped: this management event alone does not support a precise technique claim |
| Entity handling | AzureResource (TargetResourceId) and a valid optional IP (SourceIPAddress) |

[KQL](../../detections/azure/AZ-DET-010.kql) and [REST body](../../detections/azure/AZ-DET-010.json) are bound to the reviewed fixed contract. Only exact case-insensitive operation names and terminal statuses match. The operation identifiers are:

- `Microsoft.Authorization/policyAssignments/delete`

Original EventDataId is mandatory; per-run deduplication selects the latest row for each source ID. Empty original IDs are omitted and must be counted during a separately authorized live quality assessment. Caller is kept as context because its GUID/UPN/application meaning is not established by this query. IPv4/IPv6 values are mapped only when valid and not CIDR ranges; keys, claims, request bodies and secret values are never projected. AZ-DET-011 deliberately has no IP mapping after aggregation.

False positives: Approved governance migration, duplicate cleanup or retiring a non-security policy. There is no unconditional CI/administrator allowlist. Proposed exceptions must bind actor, exact scope, operation, change authorization and expiry, with regression cases. No real-data precision or false-positive rate has been measured.

Investigation: Recover the assignment purpose, enforcement mode, scope and approval from authorized change records; check replacements and exemptions. Use authorized private evidence; do not block an account, remove permissions or delete resources automatically.

Limitations: Not all policy assignments are security controls. Deletion alone cannot establish impairment; no forced technique mapping is included. These rules share overlapping one-hour lookbacks and fifteen-minute schedules. Per-run deduplication does not suppress repeats across executions; incident grouping is disabled. There is no lateness guarantee or proof of fresh telemetry. Broad single-event rules are deliberately lower-priority candidates for investigation.

Testing: `python -m portfolio` exercises explicit positive, replay, started, wrong-operation, stale and missing-lineage controls. `tests/test_portfolio.py` adds thresholds, identity/scope separation, boundary/order/tie handling and deployment fault cases. The Python reference model is not Kusto execution or live detection validation. The [portfolio validation record](../validation/detection-portfolio.md) tracks deployment evidence separately.

See [portfolio coverage, taxonomy and source references](portfolio.md). Deployment neither provisions the monitored resource nor establishes its presence in this subscription.
