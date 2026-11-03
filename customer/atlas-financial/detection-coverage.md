# Detection coverage and ATT&CK report

**Fictional customer coverage assessment; versioned-definition summary.** All
twelve rules are deployed disabled in the historical baseline. They use
AzureActivity only; the Linux transport pilot does not add endpoint coverage.
The [machine-readable inventory](coverage.json) is checked against the source
definitions by `validate.py`. Actual runtime and current state require separate
cloud evidence from the [project checkpoint](../../docs/PROJECT_STATUS.md).

| Rule / investigation behavior | Severity | Candidate API tactics | Candidate API techniques | Schedule / lookback | State |
|---|---|---|---|---|---|
| [AZ-DET-001](../../docs/detections/AZ-DET-001.md) - Azure Diagnostic Settings Modified | Medium | DefenseEvasion | T1562 | PT15M / PT1H | Disabled; incident creation false |
| [AZ-DET-002](../../docs/detections/AZ-DET-002.md) - Azure Role Assignment Created | Medium | Persistence, PrivilegeEscalation | T1098 | PT15M / PT1H | Disabled; incident creation false |
| [AZ-DET-003](../../docs/detections/AZ-DET-003.md) - Custom Role Definition Changed | Medium | PrivilegeEscalation | T1098 | PT15M / PT1H | Disabled; incident creation false |
| [AZ-DET-004](../../docs/detections/AZ-DET-004.md) - Network Security Rule Changed | Low | Unmapped | Unmapped | PT15M / PT1H | Disabled; incident creation false |
| [AZ-DET-005](../../docs/detections/AZ-DET-005.md) - Key Vault Access Policy Changed | Medium | Persistence, PrivilegeEscalation | T1098 | PT15M / PT1H | Disabled; incident creation false |
| [AZ-DET-006](../../docs/detections/AZ-DET-006.md) - Virtual Machine Run Command | Medium | Execution | T1651 | PT15M / PT1H | Disabled; incident creation false |
| [AZ-DET-007](../../docs/detections/AZ-DET-007.md) - Storage Account Keys Listed | Low | CredentialAccess | Unmapped | PT15M / PT1H | Disabled; incident creation false |
| [AZ-DET-008](../../docs/detections/AZ-DET-008.md) - Resource Lock Removed | Low | Unmapped | Unmapped | PT15M / PT1H | Disabled; incident creation false |
| [AZ-DET-009](../../docs/detections/AZ-DET-009.md) - Activity Log Alert Deleted | Medium | DefenseEvasion | T1562 | PT15M / PT1H | Disabled; incident creation false |
| [AZ-DET-010](../../docs/detections/AZ-DET-010.md) - Policy Assignment Deleted | Low | Unmapped | Unmapped | PT15M / PT1H | Disabled; incident creation false |
| [AZ-DET-011](../../docs/detections/AZ-DET-011.md) - Repeated Failed Privileged Operations | Medium | Unmapped | Unmapped | PT15M / PT1H | Disabled; incident creation false |
| [AZ-DET-012](../../docs/detections/AZ-DET-012.md) - Role Grant Followed by Diagnostic Change | High | Persistence, PrivilegeEscalation, DefenseEvasion | T1098, T1562 | PT15M / PT1H | Disabled; incident creation false |

## What this matrix means

The table mirrors the committed API properties. T1098 is used at parent level
for candidate permission manipulation; T1651 denotes cloud administration
command behavior. Legacy T1562/DefenseEvasion values are retained where the
existing Azure deployment accepted them. They are not presented as a current
complete ATT&CK taxonomy. The [portfolio mapping notes](../../docs/detections/portfolio.md)
explain diagnostic/monitoring impairment context and source references.

NSG changes, lock/policy deletion, key-list operations and generic failures
are deliberately left without forced technique claims where evidence is
insufficient. A tactic/technique label is a hypothesis for investigation, not
proof of successful adversary behavior or a quantified coverage percentage.

## Coverage dimensions and practical gaps

| Dimension | Observable behavior | Gap / analyst consequence |
|---|---|---|
| Management configuration | Role/permission, diagnostic, policy, lock and network-rule changes | A write does not reveal the full before/after delta; retrieve authorized supporting configuration before claiming impact. |
| Cloud execution/key access | VM Run Command and storage key-list actions | No guest process tree, key material or data-plane exfiltration is collected by these rules. |
| Failed privilege operations | Five distinct failures in a fixed ten-minute caller/scope bin | Failure is not necessarily authorization denial; fixed bins split boundary events. |
| Ordered administration | Grant then diagnostic change by one caller in one subscription/RG within fifteen minutes | Same RG does not establish equal target scope, actual privilege use or causality. |
| Identity | Raw Caller context and valid source IP; explicit canonical joins in synthetic RBA | Not all Caller formats identify a human; shared IP is not identity equivalence. |
| Endpoint/identity sign-ins | Synthetic examples support local correlation; one Syslog transport pilot exists | No university directory export, native SSH/authpriv, Windows/Sysmon or EDR coverage. |

## Legitimate matches and tuning

Policy remediation and approved logging maintenance can match diagnostic rules.
CI access setup and ordinary RBAC administration can match role rules. Portal
storage key access and approved Run Command support may also be legitimate.
Investigate the exact actor, target, approval, operation and event-time window.
Preserve evidence and limit any exception by those fields plus expiry; do not
whitelist an administrator or CI identity broadly.

Synthetic positive/negative/edge controls establish intended reference behavior.
They do not establish Kusto runtime, actual alert generation, production precision
or real false-positive rates. Overlapping fifteen-minute schedules and one-hour
lookbacks may surface the same source action in more than one evaluation;
within-query deduplication does not guarantee cross-run incident suppression.

## Source acceptance references

- [Actual detection deployment and preservation](../../docs/validation/detection-portfolio.md).
- [Actual historical AzureActivity rows](../../docs/validation/first-ingestion.md).
- [Actual bounded AMA Syslog proof and limits](../../docs/validation/local-linux-ama.md).
- [Synthetic correlation and controls](../../docs/validation/phase-4.md).
- [Triage and change procedure](operations.md).
