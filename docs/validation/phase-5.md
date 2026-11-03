# Phase 5: local SOAR validation

Phase 5 has a reproducible **synthetic local** acceptance path: a canonical
RBA finding becomes a durable case, investigation notes, a revision-bound
review decision, BenignPositive closure and one idempotent simulated ticket.
The workflow uses the existing Atlas Financial dataset and has no network,
Azure credentials, paid SaaS, automation rule or containment action.

## Executable acceptance

```powershell
python -m soar
python -m unittest discover -s tests -p test_soar.py -v
```

The default demonstration yields **one case, one closed case, one local ticket,
nine chained audit events and six passing failure scenarios**. A repeat against
the same store yields the same report and adds no case, ticket or audit event.
The report labels itself `synthetic-local-soar`; all finding/source IDs remain
synthetic. `safety` records zero network calls, Azure changes, Sentinel incidents
and containment actions. These values describe this offline implementation,
not an audit of unrelated Azure activity.

| Check | Observed outcome |
|---|---|
| Transient local connector | Accepted on attempt two; one ticket; retry budget persists |
| Timeout simulation | Three attempts then dead letter; reopening cannot reset the budget |
| Permanent failure | One attempt then dead letter |
| Reviewer denial | Case returns to Investigating |
| Expired decision | Case returns to Investigating without a classification |
| Conflicting finding replay | Rejected without replacing the original case |

Fourteen dedicated unit/integration tests pass locally. They cover persistence
across connection reopen, conflict rollback, non-synthetic input and broken
event lineage, state/evidence/role gates, consumed/stale/expired decisions,
note bounds/idempotency, retry budgets and ticket uniqueness, append-only audit
corruption rejection, transaction rollback on injected persistence failure,
repeatable end-to-end execution and real CLI artifact generation. These tests
exercise a local SQLite store; cloud/API behavior is not represented by fake
Azure success evidence.

The [report schema](../../schemas/soar-report.schema.json) documents public
report/evidence boundaries. The Python boundary validates input and workflow
semantics; JSON Schema is an additional artifact contract rather than the
case-state authorization mechanism. Run the repository's full suite and
required detection validator when integrating this package into a release.

## Evidence and limits

`python -m soar` writes `report.synthetic.json`, `cases.synthetic.json`,
`audit.synthetic.json`, a local SQLite store and a summary beneath ignored
`.local/soar/`. The [operations runbook](../operations/soar.md) explains their
lineage, finite retry model, state transitions and recovery boundaries.
Only deliberately selected synthetic JSON should be published as evidence;
never publish a live database or an unreviewed analyst note.

The demonstration's analyst and reviewer are fictional local roles. A local
reviewer decision is not authenticated human approval. Timeout/backoff behavior
is deterministic local simulation, not a tested remote transport deadline.
The audit chain detects ordinary tampering but cannot resist an administrator
rewriting the database. No Sentinel incident was created or classified by this
package, so this does **not** satisfy Phase 1's separate real scheduled-alert
and incident lifecycle criterion. No claim is made about production response
times, real-world detection accuracy or live SOAR integration.
