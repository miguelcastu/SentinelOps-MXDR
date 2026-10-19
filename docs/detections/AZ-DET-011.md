# AZ-DET-011 - Repeated Failed Privileged Operations

Purpose: At least five distinct failed RBAC assignment/role definition writes by one caller in one subscription/resource group and fixed ten-minute bin. These are operational failures, not necessarily authorization denials or an attack.

| Property | Contract |
|---|---|
| Source | Existing AzureActivity, management plane |
| Fixed resource UUID | `ed65b130-b1e9-540e-8015-b09bd9797d80` |
| Priority | Medium; rule priority is not an attack verdict |
| State | Disabled; incident creation false; no automation |
| Schedule / lookback | PT15M / PT1H; bounded inclusive event-time filter |
| MITRE in REST | Unmapped: this management event alone does not support a precise technique claim |
| Entity handling | Caller and resource group as investigation context; no invented Account or IP mapping for aggregated evidence |

[KQL](../../detections/azure/AZ-DET-011.kql) and [REST body](../../detections/azure/AZ-DET-011.json) are bound to the reviewed fixed contract. Only exact case-insensitive operation names and terminal statuses match. The operation identifiers are:

- `Microsoft.Authorization/roleAssignments/write`
- `Microsoft.Authorization/roleDefinitions/write`

Original EventDataId is mandatory; per-run deduplication selects the latest row for each source ID. Empty original IDs are omitted and must be counted during a separately authorized live quality assessment. Caller is kept as context because its GUID/UPN/application meaning is not established by this query. IPv4/IPv6 values are mapped only when valid and not CIDR ranges; keys, claims, request bodies and secret values are never projected. AZ-DET-011 deliberately has no IP mapping after aggregation.

False positives: Broken CI deployments, stale role references and transient service failures. There is no unconditional CI/administrator allowlist. Proposed exceptions must bind actor, exact scope, operation, change authorization and expiry, with regression cases. No real-data precision or false-positive rate has been measured.

Investigation: Inspect the exact failure/substatus with authorized private evidence, intended role/scope, caller ownership and recent legitimate changes. Use authorized private evidence; do not block an account, remove permissions or delete resources automatically.

Limitations: Five unique failures per caller/resource group in a UTC fixed ten-minute bin, not a sliding window. Failures across a bin boundary can be missed; empty subscription/caller/group/ID is excluded. Failed does not mean authorization denied. These rules share overlapping one-hour lookbacks and fifteen-minute schedules. Per-run deduplication does not suppress repeats across executions; incident grouping is disabled. There is no lateness guarantee or proof of fresh telemetry. Broad single-event rules are deliberately lower-priority candidates for investigation.

Testing: `python -m portfolio` exercises explicit positive, replay, started, wrong-operation, stale and missing-lineage controls. `tests/test_portfolio.py` adds thresholds, identity/scope separation, boundary/order/tie handling and deployment fault cases. The Python reference model is not Kusto execution or live detection validation. The [portfolio validation record](../validation/detection-portfolio.md) tracks deployment evidence separately.

See [portfolio coverage, taxonomy and source references](portfolio.md). Deployment neither provisions the monitored resource nor establishes its presence in this subscription.
