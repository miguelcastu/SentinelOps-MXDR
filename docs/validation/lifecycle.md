# Verified scheduled-alert and incident lifecycle

Accepted on **3 November 2026**. The event is explicitly synthetic; Kusto
matching, scheduling, the security alert, Sentinel incident and classified
closure are actual Azure behavior. This was one isolated platform acceptance
test. The twelve security definitions were not activated.

## Event-to-closure evidence

All times are UTC on 3 November. Private Azure IDs and portal URLs remain
outside the public repository.

| Stage | Actual result | Evidence |
|---|---|---|
| Test input, 19:12:41 | One labeled inline datatable row and fictional account; no customer table or new ingestion batch | Fixed reviewed query, verified persisted body and query SHA |
| KQL match | One search-result row | [Detailed read-only investigation](../../evidence/completion/alert-investigation.sanitized.json) |
| Scheduled alert, 19:19:09 | One actual Azure Sentinel / Scheduled Alerts alert; title, rule and event time match | Actual related-alert response, summarized in the investigation |
| Incident | One real linked incident; exact rule/workspace/time and service alert count verified | [Final OIDC metadata and reconciliation record](../../evidence/completion/lifecycle-start.sanitized.json) |
| Investigation | Source query/run, match, alert and incident reconcile to the approved synthetic test | Personal MFA read-only verification; hashed query/incident joins |
| Classification, 19:33:13 | Closed / BenignPositive / SuspiciousButExpected | [Successful OIDC classification](https://github.com/miguelcastu/SentinelOps-MXDR/actions/runs/41704210239), [actual response](../../evidence/completion/lifecycle-close.sanitized.json) |
| Timeline reconciliation, 20:07:05 | First/last activity restored to 19:12:41 on the already closed incident; classification preserved | [Successful OIDC reconciliation](https://github.com/miguelcastu/SentinelOps-MXDR/actions/runs/41709469491), final record above |
| Final preservation, 20:10:19 | Test disabled, original rules/settings preserved, exact incident closed, timeline verified and VM off | [Independent 76-check audit](../../evidence/completion/final-preservation.sanitized.json) |

Creation and activation originated in [OIDC recovery run
41701030513](https://github.com/miguelcastu/SentinelOps-MXDR/actions/runs/41701030513),
commit `2e457a28046d7168fccd24e813b6ee2e878de56d`. Its later detailed-alert
observation step was denied after Azure had produced the alert and incident.
That run remains a failed job in the evidence history; the backend outcome was
verified separately, rather than relabeling the job successful.

The detailed investigation used a snapshot recorded at **19:23:01** and reviewed
at **19:33:42**. The snapshot predates classification and preserves the original
alert/activity values. The original classified closure at **19:33:13** remains
the actual classification time; the later repair is a separate operation.

A Defender incident URL was supplied by Azure, but the Defender portal UI was
not opened. Acceptance rests on Sentinel REST and actual alert evidence, not a
portal screenshot. The roughly six-minute test-to-alert interval is one sample,
not a measured service-level objective.

## Authority and least privilege

The operator approved the concrete PR #20 proposal with "autorizo las pruebas
que necesites, cualquiera". Only fixed LAB-VAL-001 was temporarily enabled.
Twelve managed security definitions stayed disabled and Fusion was preserved.
Creation, activation, classification and reconciliation used protected-main
GitHub OIDC. Personal MFA was confined to approved administrative setup and
read-only verification, including the detailed investigation.

The existing CI identity and immutable federation were reused. Four additional
exact assignments cover the test rule writer, owned-workspace incident reader,
query-execution gate and classifier at only the actual test incident. No
workspace-wide incident writer, broad Reader/Contributor or table-data grant
was added. See [setup](../../evidence/completion/lifecycle-setup.sanitized.json),
[classifier setup](../../evidence/completion/lifecycle-classifier-setup.sanitized.json)
and the final additive-access audit. Microsoft documents the distinction
between [query execution and table access](https://learn.microsoft.com/azure/azure-monitor/logs/manage-table-access#configure-table-level-access-dual-role-method).

## Failures and corrections

1. [First run 41697635395](https://github.com/miguelcastu/SentinelOps-MXDR/actions/runs/41697635395)
   created the target disabled, then enable returned Unauthorized. Actual
   management metadata identified missing query-execution permission. Cleanup
   passed; the [first-attempt record](../../evidence/completion/lifecycle-first-attempt.sanitized.json)
   remains historical evidence.
2. Protected PR #21 added only workspace `query/read`, with empty DataActions.
   Recovery required the prior query's exact SHA, verified disabled/alertless
   state, and consumed that reference when the fresh bounded query persisted.
3. Recovery produced the actual alert and incident, but CI's detailed-alert POST
   was denied. The authorized session verified those details read-only. CI
   observation was changed to rule/incident metadata GETs; broader detailed-alert
   or entity permissions were not granted.
4. The original closure PUT omitted optional first/last activity timestamps.
   A later metadata check found they no longer represented the verified source
   event. The correction preserves those fields on future closures and provides
   an explicit, digest-bound reconciliation for this one already closed case.
   It restored both timestamps from the original snapshot, source query and
   alert evidence using **one exact-incident PUT**, then read back the result.
   Status and classification stayed unchanged. No reactivation, new event,
   additional role or new ingestion was required.

The read-only infrastructure verifier performs six GETs. The metadata-only
observer also uses GETs. **The final successful lifecycle proof used `reconcile`,
which includes the single incident PUT described above**; it must not be reported
as a purely GET-only observation run. Its source/run and original scheduled
execution are recorded separately in the public reconciliation evidence.

## Completion controls and limits

The test query expires after twenty minutes. Polling and workflow duration are
finite; finally/always-disable and bounded read-back protect failure paths.
The rule is now disabled. Completed recovery, AMA and KQL ledgers remain consumed.
[GitHub closeout](../../evidence/completion/github-closeout.sanitized.json) removed
the lifecycle approval gate, recovery/reconciliation references and exact-incident
identifier secret. Existing Azure OIDC configuration and all 22 Azure assignments
were preserved. There is no recurring sender or further authorization to replay
the test.

This establishes one real platform lifecycle using a labeled test event. The
twelve definitions separately passed [bounded KQL runtime validation](live-kql-portfolio.md).
Their production precision, recall and active scheduled-alert behavior are not
inferred from the isolated lifecycle test. No attack, containment, university
telemetry collection, source expansion or paid add-on was introduced.
