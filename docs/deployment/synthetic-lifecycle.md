# Isolated scheduled-alert and incident acceptance

This is a concrete **approval-gated proposal**, not executed cloud evidence.
The 3 November request authorizes completing the project and a maximum budget;
the permanent project policy separately requires explicit rule-activation and
new-access scope. No activation or role setup is inferred from an estimate.
The prepared code can be reviewed before that final decision.

## Exact scope

- One new fixed `LAB-VAL-001 - Synthetic lifecycle acceptance` Scheduled rule,
  UUID in [the fixed contract](../../lifecycle/contract.py). None of the twelve
  existing detection definitions is enabled or edited; Fusion is preserved.
- One explicitly labeled inline `datatable` event and one fixed fictional
  account. No customer table is scanned, no machine is started, no new source
  or log batch is sent, and no security control is changed to generate a match.
- Five-minute scheduler, thirty-minute query period, threshold greater than
  zero, one grouped incident. The query becomes empty twenty minutes after
  its fixed start. Observation is limited to 24 metadata polls, thirty seconds
  apart; the workflow has a twenty-minute timeout.
- After actual alert/incident linkage is read back, finally disable the test
  rule. A separate always-cleanup step verifies it. Do not delete it or replay
  the test: an existing target stops `start` before creation/activation.
- Investigate only the exact linked synthetic incident, then close through
  OIDC as `BenignPositive / SuspiciousButExpected`. Preserve a sanitized actual
  response, its workflow source/run and a common hashed test-run reference.
  No containment, email, account block, playbook or external ticket.

This proves the real scheduler -> alert -> Sentinel incident -> classification
path **if it succeeds**. It does not measure the twelve detections' real-data
accuracy or establish native endpoint monitoring. A Defender portal incident
URL is reported only if Azure actually supplies it; Sentinel REST evidence
alone does not prove a human opened Defender.

## Permissions and authentication

The existing `id-sentinelops-ci` and immutable main-only environment trust are
reused. The [preview-first setup](../../scripts/prepare_lifecycle.py) never
deploys an analytics rule. Proposed additions are:

| Assignment | Exact action/scope |
|---|---|
| Reused analytics writer | Existing read/write actions at only the fixed test-rule resource |
| New incident reader | `Microsoft.SecurityInsights/incidents/read` at the existing lab workspace; this permits incident metadata inventory in that workspace |
| Later classifier | Incidents read/write at **only the actual linked test incident**, after it exists and the rule is disabled |

No workspace-wide incident writer, role-management permission for CI, extra CI
identity, customer-log query permission or broad rule writer is proposed.
The classifier identifier is placed in a GitHub environment secret, not the
repository. No personal deployment fallback is allowed. Azure rejected a
missing DCR scope in the earlier AMA work; if it similarly rejects the missing
rule's exact RBAC scope, stop and report it. A broad grant or one-time personal
rule creation is **not** included in this proposal.

The [manual main-only workflow](../../.github/workflows/validate-lifecycle.yml)
defaults to `disable` and requires an explicit confirmation and exact contract
fingerprint before authentication. No schedule, live sender or PR OIDC access.
Personal MFA is confined to approved administrative RBAC setup/verification.

## Cost and subscription gate

Actual 3 November read-only REST found the same Enabled subscription, spending
limit On, published EUR 175.99436818021823 and credit expiry 12 November
18:00:16 UTC. [Eligibility](../../evidence/completion/eligibility.sanitized.json)
and [baseline](../../evidence/completion/baseline.sanitized.json) are point-in-time
records; closed credit can lag usage. The operator's EUR175 maximum is preserved.

The proposal adds **zero ingested message bytes**, Azure compute, Logic Apps,
paid connectors, plans or recurring collection. The inline query scans zero
customer tables. Planning allowance is **EUR1 maximum reserved within the
operator's EUR175 total**, rather than using the remaining balance as a target;
the expected incremental service cost is near zero, but this is not an invoice
or an Azure-enforced custom euro cap. Do not execute if current eligibility,
subscription state, expected workload or cost cannot be checked safely. Never
upgrade, switch subscriptions, remove the spending limit, or change caps,
pricing, retention, diagnostics or budgets. No test should start close enough
to expiry that its cleanup window would cross the expiry.

## Controlled execution after approval and protected merge

1. Record the exact approval/fingerprint privately; never create that record
   merely because code or a PR exists. Freshly verify financial eligibility.
2. Run setup preview, then approved setup from clean merged main. Verify exact
   assignments and existing trust; stop on 404 or other rejected scope.
3. Dispatch `start` once. Retrieve only sanitized workflow evidence; retain
   private incident IDs locally. A no-incident timeout is an unaccepted test,
   not an excuse to rerun or activate a different rule.
4. Confirm actual test-rule disabled state. Review the one incident's title,
   exact workspace/rule link, original test time and linked actual alert.
5. Prepare the one exact incident classifier assignment, then dispatch `close`.
   Read back Closed/classification/reason. No permission broadening on failure.
6. Independently verify all original thirteen rules, workspace settings,
   subscription/credit, VM poweroff and no new paid service. Remove the
   lifecycle approval variable in GitHub after evidence delivery so the
   completed release does not retain an armed test gate.

The completed [AMA ledgers](../validation/local-linux-ama.md) are unrelated and
must never be reset/reused. The test workflow code, mocks and this proposal do
not satisfy Phase 1 until dated actual start and classified-closure evidence exist.

API references: [scheduled rule request](https://learn.microsoft.com/rest/api/securityinsights/alert-rules/create-or-update?view=rest-securityinsights-2025-09-01),
[incident alerts](https://learn.microsoft.com/rest/api/securityinsights/incidents/list-alerts?view=rest-securityinsights-2025-09-01),
[incident classification](https://learn.microsoft.com/rest/api/securityinsights/incidents/create-or-update?view=rest-securityinsights-2025-09-01).
