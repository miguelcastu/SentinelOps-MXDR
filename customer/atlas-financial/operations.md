# Analyst operations and controlled engineering changes

**Exercise runbook.** These procedures operate on clearly labeled local cases
unless a separately authorized actual incident is identified. No notification
is sent and no containment operation is executed by following the offline demo.

## Triage workflow

1. Establish the evidence class: actual cloud response, actual local observation,
   synthetic fixture, mocked transport or design-only artifact. Preserve this
   class in every downstream note.
2. Verify intake identity, source event IDs and payload fingerprint. Repeated
   identical intake must return the existing case; an ID reused with conflicting
   evidence must fail, not overwrite the first investigation.
3. Establish event order and affected entity/scope. Distinguish raw Caller
   values from canonical mapped accounts; shared IP alone is not an identity join.
4. Read source-health uncertainty. Missing/Unknown telemetry lowers confidence
   and opens a collection investigation; it does not erase an observed risk.
5. Determine impact and urgency from the evidence. A High RBA priority means
   the configured heuristic threshold was met, not a calibrated likelihood of
   compromise or proof of business impact.
6. Assign an investigation owner and record the next action. For a synthetic
   example, keep all actor/host names fictional and preserve the label in exports.

## Investigation worksheet

Use this structure in the case's notes or a controlled service ticket:

```text
Case ID / evidence class / analyst role:
Finding rule and version / intake fingerprint:
Detection time / original event times (UTC):
Canonical identity / source identity formats / mapping evidence:
Affected resource and exact administrative scope:
Original event IDs / chain order / supporting artifact paths:
Approved change ID / owner / operations / validity window:
Observed action and outcome:
Alternative benign explanations:
Collection health and missing evidence:
MITRE candidate behavior and mapping uncertainty:
Impact assessment / decision / approver / action limitations:
Verdict / closure rationale / residual risk / follow-up owner:
```

For AZ-DET-002/003/005, inspect the actual permission/role delta and effective
scope before saying escalation occurred. For AZ-DET-001/009/012, establish
whether visibility decreased rather than inferring it from a write/delete.
For AZ-DET-004, inspect direction, ports, priority and effective reachability.
For AZ-DET-006, control-plane Run Command evidence does not reveal the full
guest execution result. Full per-rule questions are in the
[detection catalog](../../docs/detections/portfolio.md).

## Response decision and escalation

| Condition | Exercise action | Actual Azure boundary |
|---|---|---|
| Unapproved privilege + reduced visibility + supporting host evidence | Escalate to service owner; recommend preserving evidence and reviewing access | No automatic disable/isolation; exact human authorization required. |
| Legitimate change matches logic | Record benign positive and the approved change | Do not silence all CI activity or the whole maintenance window. |
| Faulty parsing or wrong identity join | Record false positive only after demonstrating the logic error; open tuning change | No deployment from the case adapter. |
| Insufficient source/identity evidence | Keep verdict Undetermined; state the gap and collection investigation | Do not claim safety from missing telemetry. |
| Source path failure / drift | Escalate to platform owner and preserve the configuration snapshot | Do not disable logging to reproduce the failure. |
| Budget/credit uncertainty | Stop proposed cloud experiments; notify operator in the exercise notes | No upgrade, spending-limit removal or subscription switch. |

The case workflow's approval is a recorded application decision, not an Azure
token. A recommended action remains a recommendation until an authorized
operator acts through a separately reviewed channel. No destructive adapter is
present. Avoid real recipient details in public tickets.

## Closure quality gate

Close only with an evidence-backed classification and a specific rationale:

- **True positive:** evidence supports the simulated or real malicious behavior;
  distinguish “synthetic true positive” from a confirmed production incident.
- **Benign positive:** the detection correctly matched an authorized activity.
- **False positive:** a demonstrated parsing, logic or entity-association error
  caused an incorrect finding; record the corrective test.
- **Undetermined:** evidence cannot justify a stronger conclusion. Preserve
  uncertainty and follow-up work rather than inventing a verdict.

Record unresolved evidence gaps, review/audit trail and follow-up owner. A local
closed case does not prove a Sentinel incident was closed. Actual Sentinel
classification vocabulary and permissions must be checked by the live adapter,
not inferred from these local terms.

## Detection tuning / change control

Every change record includes problem, scope, old/new hashes, data prerequisites,
expected legitimate matches, synthetic controls, cost/permission effects,
rollback, approver, exact PR head/CI and actual post-deployment verification.

1. Reproduce the problem offline and preserve the original event lineage.
2. Test a positive, a benign lookalike, a near miss and a boundary case.
3. Bind any exception to actor, operation, exact target, change ID and expiry.
   Keep event history available; do not erase the risk or exempt an entire role.
4. Review code in a feature branch and require offline CI before normal merge.
   Matching source definitions are not evidence that Kusto executes them.
5. Deploy only through the approved main-only OIDC workflow and exact target;
   preserve the disabled baseline unless the specific activation is authorized.
6. Read back actual persisted state. On failure stop at the observed boundary;
   do not silently broaden RBAC, create a replacement resource or force a push.
7. Roll back only the authorized managed properties, with a matching before-state
   and concurrency protection. Resource deletion is not a default rollback.

## Platform incident playbook

Follow source -> export/agent -> routing/DCR -> workspace/table -> query/time
window -> rule runtime -> case workflow. For a quiet event-driven source, zero
rows are not proof of failure. A powered-off guest has no freshness obligation;
its existing DCR can resume collection at boot. In a delayed bounded pilot,
inspect counts and configuration and wait within the approved query budget;
never replay a consumed sender ledger to force apparent progress.

The [health runbook](../../docs/operations/platform-health.md) contains thresholds
and safe faults; [service assurance](service-assurance.md) defines the reporting
denominators. For an actual security incident, preserve private evidence first
and use the operator's approved communications plan outside this fictional lab.
