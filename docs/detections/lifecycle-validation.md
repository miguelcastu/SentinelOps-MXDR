# Phase 1 audit and controlled incident test proposal

**Current state: partially complete.** Both disabled rules match their versioned REST bodies, including KQL, MITRE techniques, schedule, custom details, entity mapping and incident settings. The read-only Azure audit on 18 October 2026 found one instance of each rule and no managed-property drift. No real alert or incident was generated in this phase.

| Rule | Schedule / lookback | MITRE API parent | Entities | Incident creation |
|---|---|---|---|---|
| AZ-DET-001 | 15 min / 1 hour | T1562, Defense Evasion | AzureResource + valid IP | Disabled |
| AZ-DET-002 | 15 min / 1 hour | T1098, Persistence / Privilege Escalation | AzureResource + valid IP | Disabled |

Both include operation, status, caller, correlation ID and event ID as custom alert details. Caller is deliberately retained as context rather than automatically mapped to an Account because AzureActivity can report different principal formats. Diagnostic tampering and role-grant subtechniques remain documented context; the actual API accepts parent techniques here. Neither rule proves malicious intent or role privilege by itself.

## Synthetic triage findings

```powershell
python -m scripts.assess_detections
```

[Eight labeled scenarios](../../tests/fixtures/detection_triage.json) demonstrate one benign match, one suspicious match, one benign nonmatch and one missed suspicious **failed operation** for each rule. A limited interpreter evaluates the approved filters; it does not execute Kusto. The failed-attempt gap is intentional for these success-only rules and is a candidate for a separate detection, not a silent change to existing coverage. These counts are not production precision, recall or real false-positive rates.

Policy remediation and approved diagnostic changes match AZ-DET-001. Approved CI access and ordinary RBAC administration match AZ-DET-002. Do not broadly exclude the CI identity or all maintenance hours: an attacker could reuse them. Investigate change approvals, exact affected scope, role definition and initiating identity before tuning. A future expiring exception must bind all of those fields and have positive/negative regression cases.

AZ-DET-001 removes exact duplicate rows within a run. AZ-DET-002 does not; both one-hour windows overlap the 15-minute schedule. Most matched events can recur in four evaluations, with an inclusive boundary potentially appearing in five. SingleAlert aggregates only within an evaluation; disabled incident grouping does not suppress cross-run duplicates. Leave deployed grouping unchanged until actual volume and incident behavior can be measured. Any eventual grouping by correlation ID/event ID must preserve independent operations; do not deduplicate all events from an actor together.

## Explicitly pending approvals

The supplied mission requires approval before activating a rule, changing logging, introducing a workload or expanding RBAC. Current `AGENTS.md` also permits only disabled-rule deployment. The following is a proposal, not execution authorization:

1. Approve a one-time, maximum 45-minute AZ-DET-002 test and a dedicated gated OIDC workflow that temporarily enables this exact rule and incident creation, with ETag checks, private before-state, bounded polling and verified restoration. Keep AZ-DET-001 disabled and preserve Fusion. Prepare and review that implementation before execution. A runner interruption still needs a documented operator restoration path; never promise that `finally` alone guarantees restoration.
2. Approve **read-only validation permissions first**, separately from the rule deployer: only AzureActivity, SecurityAlert and SecurityIncident queries plus Sentinel incident read, on the existing workspace. Validate table-specific query permissions using Microsoft's current authorization model before assigning them. Preserve the existing detection CI roles; do not use personal Owner access to bypass this gate.
3. Approve the test event: create one temporary assignment of the **existing workspace-metadata-reader custom role** at the **exact existing workspace** to the operator's existing principal, provided verification confirms that principal already has effective Owner permission there. This adds no effective privilege, creates a roleAssignments/write event, and does not alter logging. Require administrative MFA and authorization to remove only that exact temporary assignment afterwards. Stop if it already exists, its effective permissions differ or another owner manages it. Do not grant a new administrator role, create a principal or assign anything at subscription scope.
4. Investigate the resulting actual alert and Sentinel incident. Defender portal visibility is a separate check: verify workspace onboarding rather than claim that an ARM incident alone proves Defender UI integration.
5. Once the actual incident ID is known, request/verify permission to annotate and close **that incident only** with a justified test classification (typically benign positive / suspicious but expected test activity). Do not close unrelated incidents or grant workspace-wide incident write implicitly.

AzureActivity is an ingestion-exempt table and Analytics interactive queries have no scanned-data fee under the [documented pricing model](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/cost-logs). Reconfirm the actual plans and meter before this test; no paid feature or recurring workload is authorized by this document. Use existing telemetry where possible and at most a fixed set of aggregate queries. No activation/query test has been run in this phase.

## Required evidence before acceptance

Record event time, unique event/correlation IDs privately, rule ID/version and run window; prove the event matches KQL; fetch the actual scheduled-rule alert and linked incident; investigate scope/identity/change authorization; record verdict and authorized classification; remove only the approved temporary assignment; restore the exact disabled rule body and confirm no drift. Publish a sanitized timeline with actual timestamps and API/workflow references. If any link is missing, Phase 1 remains incomplete.
