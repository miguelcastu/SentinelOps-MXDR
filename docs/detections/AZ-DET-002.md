# AZ-DET-002 — Azure Role Assignment Created

Status: **deployed and disabled**, verified through the existing OIDC identity and the actual Azure API. No live false-positive rate has been measured.

## Purpose, source and logic

Detect successful `Microsoft.Authorization/roleAssignments/write` operations in the existing `AzureActivity` table. This is a broad change-monitoring detection: it does not claim every role assignment is privileged or malicious. It requires no new connector, VM, data source or telemetry ingestion.

The [KQL](../../detections/azure/AZ-DET-002.kql) and [REST definition](../../detections/azure/AZ-DET-002.json) are synchronized. Exact case-insensitive operation matching, `Success`/`Succeeded` statuses, an inclusive one-hour event-time window and a 15-minute schedule are enforced. Severity is Medium. The rule and incident creation stay disabled; no playbook is attached.

## MITRE and entities

[T1098.003 Additional Cloud Roles](https://attack.mitre.org/techniques/T1098/003/) maps to Persistence and Privilege Escalation. The REST payload uses its parent **T1098**, because the observed Sentinel API accepts T#### technique values rather than subtechnique IDs. Successful Azure RBAC changes are a relevant observation; this query alone does not establish the actor's intent or whether privileges increased.

AzureResource maps `TargetResourceId` to `ResourceId`; IP maps the validated `SourceIPAddress` to `Address`, excluding invalid/CIDR input. `Caller` remains a custom detail because it can represent users or services. The resource can identify the role-assignment object rather than the underlying permission scope. No grantee account, assigned role name or privilege level is inferred from absent fields.

## False positives and testing

Expected benign matches include approved administrator changes, Azure Policy managed-identity grants, infrastructure pipelines and access-provisioning automation. One synthetic fixture explicitly verifies that legitimate administration **also matches**. Failed, started, accepted, read, delete, role-definition and unrelated diagnostic operations do not match.

The 17 synthetic fixtures exercise mixed case, status variants, exact matching, time boundaries and ordinary administration. Offline interpretation is limited to filter semantics; it is not real Kusto execution. To assess actual false positives later, an approved read-only identity must compare aggregate hit counts against approved change records. Do not suppress all role-assignment changes or guess a production false-positive percentage from synthetic data.

## Deployment and limitations

The operator authorized one new detection. Its reviewed, fixed resource UUID is `5a347e1c-bc1e-53ab-80a1-d6fd619eb91c`; this is a new lab rule identifier, not a tenant or subscription ID. The workflow checks the complete existing inventory before writing; a duplicate display name, conflicting ID, enabled target, unreadable inventory or pagination stops the deployment. Updates use the observed etag; initial creation sends `If-None-Match=*`. No concurrent same-name creation by another system is allowed; REST conditional-header behavior still needs actual lab evidence.

The one-hour window overlaps across runs and can miss events delayed more than an hour. Cross-run deduplication and dynamic allowlists are not implemented. An enabled rule would need separate operational and cost approval. See the [one-time connection runbook](../deployment/second-detection-test.md).
