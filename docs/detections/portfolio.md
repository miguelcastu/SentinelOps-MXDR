# AzureActivity detection portfolio

The operator requested detection breadth before SOAR on 19 October 2026. The portfolio adds ten fixed disabled definitions to the two existing disabled rules. All twelve are now verified in Azure through [actual deployment and preservation evidence](../validation/detection-portfolio.md). Existing Fusion remains outside managed scope. A deployed disabled definition is not active coverage or an emitted alert.

| Detection | Behavior | Priority | Logic |
|---|---|---|---|
| [AZ-DET-001](AZ-DET-001.md) | Diagnostic settings modified | Medium | Existing single-event rule |
| [AZ-DET-002](AZ-DET-002.md) | Role assignment created | Medium | Existing single-event rule |
| [AZ-DET-003](AZ-DET-003.md) | Custom Role Definition Changed | Medium | single |
| [AZ-DET-004](AZ-DET-004.md) | Network Security Rule Changed | Low | single |
| [AZ-DET-005](AZ-DET-005.md) | Key Vault Access Policy Changed | Medium | single |
| [AZ-DET-006](AZ-DET-006.md) | Virtual Machine Run Command | Medium | single |
| [AZ-DET-007](AZ-DET-007.md) | Storage Account Keys Listed | Low | single |
| [AZ-DET-008](AZ-DET-008.md) | Resource Lock Removed | Low | single |
| [AZ-DET-009](AZ-DET-009.md) | Activity Log Alert Deleted | Medium | single |
| [AZ-DET-010](AZ-DET-010.md) | Policy Assignment Deleted | Low | single |
| [AZ-DET-011](AZ-DET-011.md) | Repeated Failed Privileged Operations | Medium | burst |
| [AZ-DET-012](AZ-DET-012.md) | Role Grant Followed by Diagnostic Change | High | sequence |

Eight new individual management-event signals, one distinct-event failure threshold and one ordered cross-operation correlation provide different investigation cases. Scope is Azure control-plane administration, not endpoint, identity-sign-in or data-plane coverage. A diagnostic write is not necessarily disabling logs, an NSG write is not necessarily internet exposure, and a role write does not establish escalation. The priority and ATT&CK labels are hypotheses requiring investigation.

## Data, costs and onboarding decision

All twelve use the existing AzureActivity table and existing subscription diagnostic export. Microsoft lists Azure Activity Logs/AzureActivity as free Sentinel data. No new source is needed for this increment. No diagnostic, ingestion, retention, cap, pricing, subscription plan or budget setting is changed. Rules remain disabled, incidents false; no recurring query or response workload is introduced. Existing subscription usage can still accrue costs; this increment does not establish a refreshed balance or a zero Azure invoice.

| Candidate | Decision | Reason |
|---|---|---|
| Existing AzureActivity | Reuse | Existing export and historical ingestion evidence; current event freshness remains unmeasured |
| Entra sign-ins/audit | Defer | Licensing, diagnostic collection and billable raw-log implications are unverified; not necessary for these rules |
| Defender alerts / Microsoft 365 audit | Defer | Free alert/audit ingestion does not provide licenses, populated sources or free underlying raw logs |
| Synthetic authentication | Keep offline | Proposed DCR/table requires separate approval; no cloud onboarding or upload |
| Endpoint/CEF/Syslog | Defer | No authorized agent, host or collector; no VM/paid resource is created to populate a demo |

Runbooks describe monitored resource prerequisites and data-path gaps. The existence of VM/Key Vault/storage/NSG rules does not prove those resources exist here. Coverage is potential until applicability, event arrival and query behavior are verified with authorized evidence. Synthetic tests do not measure operational precision.

## Deployment and recovery

`portfolio/catalog.py` fixes the ten IDs, operations, queries and disabled REST bodies. Validation compares the complete body and synchronized KQL; the shared skeleton must also satisfy the original strict AZ-DET-002 schema. The environment approval is a SHA-256 fingerprint of all definitions and targets. No arbitrary rule/query/template/UUID input is accepted.

1. Review code and all fixed UUIDs below; run offline CI, approve and merge through protected main. A manual-only workflow prevents a merge from automatically creating resources.
2. `python -m scripts.prepare_portfolio` previews without cloud requests. With the user's deployment request and valid MFA, `--apply` reuses the existing identity/trust/custom role and adds only ten exact alert-rule assignments. It validates subscription pin, protected GitHub main/environment, trust, complete inventories, original rule state and existing narrow permissions. No new identity, role definition, query permission or broad workspace write is granted.
3. Dispatch `deploy-portfolio.yml` on main. Existing OIDC, main-only environment and deployment concurrency apply. Preflight the entire batch; refuse enabled, duplicate, wrong-ID, template-managed or drifted existing targets. Create missing targets only with `If-None-Match: *`; unchanged matching targets require no PUT.
4. Verify each PUT response, subsequent GET and final inventory. Existing non-portfolio rules must be unchanged. Emit only sanitized IDs/names/states and the approved fingerprint; no tenant/subscription/telemetry appears in the evidence.

There is no automatic retry, activation or deletion. An interrupted batch may leave a verified subset disabled. Re-run only after reviewing the failure and confirming ownership/state; matching resources are skipped. ETag is required for pre-existing targets, but matching definitions are never updated. Removal is a separate operator decision, not a rollback implemented here. No user secrets are printed or copied into the repository.

The existing read-only health workflow includes all twelve managed definitions when its environment fingerprint matches. It still uses only workspace metadata and analytics inventory GETs. Without approval it retains its original two-rule scope; a nonempty stale fingerprint is an explicit configuration problem. Overall runtime/telemetry health remains Unknown.

## Reviewed fixed targets

| Detection | UUID |
|---|---|
| AZ-DET-003 | `9816cc5e-3304-5e27-b7a2-8d4a267c812b` |
| AZ-DET-004 | `f99041ea-187d-5462-9fb7-6c29f431b515` |
| AZ-DET-005 | `2c1170e0-1592-57b7-8b8e-bd3e0178cb0b` |
| AZ-DET-006 | `8e0e18f1-1d32-5c54-9f6a-98f52ef3ea6e` |
| AZ-DET-007 | `4045d337-3c91-50c6-9a6d-cb434cd985d6` |
| AZ-DET-008 | `11169c66-cfdb-5b40-94ec-4d01c3845503` |
| AZ-DET-009 | `765a60b1-d0e9-5cac-9baf-c790fd2e80cf` |
| AZ-DET-010 | `5eee8a54-76d0-53a6-8262-29b34d3bd7b9` |
| AZ-DET-011 | `ed65b130-b1e9-540e-8015-b09bd9797d80` |
| AZ-DET-012 | `eed467bf-df6d-5fa9-8957-6c916e680bcc` |

Portfolio fingerprint: `6b56d6e2b2dde1e215b4d644723828e81c41b32ef6c46b38655cced80a63e37e`.

## MITRE and primary references

T1098 is a parent-level candidate for permission manipulation; additional cloud roles are documented as T1098.003. The deployment uses parent IDs, consistent with the existing Azure API acceptance evidence. T1651 directly covers VM cloud administration commands. The API-compatible legacy T1562/DefenseEvasion mapping for alert impairment and the sequence is distinct from the current MITRE defense-impairment taxonomy; diagnostic modification alone does not prove impairment. Uncertain changes (NSG, locks, policy deletion, generic failures, storage key listing) are not forced into unsupported techniques. No percentage of ATT&CK coverage is claimed.

- [AzureActivity schema](https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/azureactivity)
- [Sentinel free data sources and billing](https://learn.microsoft.com/en-us/azure/sentinel/billing#free-data-sources)
- [Authorization/monitoring operations](https://learn.microsoft.com/en-us/azure/role-based-access-control/permissions/management-and-governance)
- [Network security rule operations](https://learn.microsoft.com/en-us/azure/role-based-access-control/permissions/networking)
- [Key Vault access-policy operations](https://learn.microsoft.com/en-us/azure/role-based-access-control/permissions/security)
- [Compute operations](https://learn.microsoft.com/en-us/azure/role-based-access-control/permissions/compute)
- [Storage key-list operations](https://learn.microsoft.com/en-us/azure/role-based-access-control/permissions/storage)
- [MITRE additional cloud roles](https://attack.mitre.org/techniques/T1098/003/)
- [MITRE cloud administration command](https://attack.mitre.org/techniques/T1651/)
- [Current MITRE cloud-log impairment](https://attack.mitre.org/techniques/T1685/002/)

References checked on 19 October 2026. See [validation and actual-cloud status](../validation/detection-portfolio.md) and [project status](../PROJECT_STATUS.md).
