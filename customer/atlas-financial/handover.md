# Engineering handover and controlled closure

**Operator handover for the personal lab.** No command here deletes cloud
resources, cancels a subscription or upgrades billing. Fictional customer
sign-off is separate from the real operator's account decisions.

## Handover inventory

| Area | Location / operating facts | Successor action |
|---|---|---|
| Authoritative checkpoint | [PROJECT_STATUS](../../docs/PROJECT_STATUS.md), [AGENTS](../../AGENTS.md) | Read before any command; later verified evidence supersedes old snapshots. |
| Rule contracts | [Twelve-rule catalog](../../docs/detections/portfolio.md), `detections/azure/` | Preserve fixed targets and disabled baseline; do not invent new UUIDs. |
| Actual cloud evidence | [Portfolio](../../evidence/detection-portfolio/), [AMA](../../evidence/local-linux-ama/) | Check observation timestamps and evidence boundary. |
| OIDC and permissions | [Security boundary](../../docs/security.md), `.github/workflows/` | Review all additive assignments; do not create a new identity or permanent secret. |
| Local machine | [AMA runbook](../../docs/onboarding/local-linux-ama.md) | Guest is stopped; existing services/DCR resume at boot. No second batch is authorized by the completed pilot. |
| Private material | Ignored `.local/`: subscription pin, SSH key, snapshots and consumed ledgers | Keep private backup encrypted; do not copy into public release. |
| Health / RBA | [Health](../../docs/operations/platform-health.md), [RBA](../../docs/operations/risk-correlation.md) | Reproduce simulations locally; Unknown is not a green health result. |
| Customer artifacts | This directory | Validate links, ticket schema, coverage and explicit fiction labels. |

## First fifteen minutes for a successor

1. Confirm repository status and current branch; preserve unrelated local work.
2. Read the checkpoint, permanent constraints and latest validation record.
3. Run the required unit tests and restricted detection validator locally.
4. Run the offline ingestion, portfolio, health and RBA CLIs and inspect their
   evidence-class fields. Do not dispatch deployment workflows as a demo.
5. Run `python customer/atlas-financial/validate.py` and inspect the eight
   fictional service tickets against the coverage and evidence links.
6. Review open acceptance gates and decide which are actual cloud versus local.
   Consult the [portfolio tour](../../docs/portfolio/demo-five-minutes.md).

## Recovery principles

A fresh checkout can reproduce the offline demonstration with Python 3.12+.
Generated files go to ignored local state. Do not recover a cloud environment
by reusing someone else's private IDs, bootstrapping duplicate identities or
replaying consumed ingestion ledgers. A backup copy of a ledger must preserve
its completed/ambiguous state; replacing it with an empty file is not recovery.

For a partial cloud deployment, first inspect actual persisted resources and
compare their reviewed owner/contract. Retry only the same authorized fixed
operation when the prior outcome is known; matching resources require no PUT.
Unexpected ownership, enabled state, missing baseline or ambiguous response
requires a stop and review. Follow the implementation's rollback/recovery
runbook; never infer that a source-code revert alone restored Azure.

For local case-state recovery, preserve the complete database plus audit data
and schema/version together. An export is a report, not necessarily a restorable
database. Re-run intake only through its idempotency checks. Do not treat a
rehydrated synthetic case as a live Sentinel incident.

## Before the operator closes Azure access

- Confirm the final PR/commit/release and its passing checks; keep a local clone
  and a safe copy of public evidence. Verify that all live claims have dated
  responses and limitations; document gates that were never executed.
- Save private operational records separately if needed, with credentials and
  identity fields protected. Do not preserve access tokens as evidence.
- Keep the local VM powered off. Leave the approved pilot and one-time bootstrap
  ledgers consumed; no autostart or repeating sender is needed for the portfolio.
- Inspect active/queued GitHub runs before closure. Existing manual workflows
  can fail after access is revoked; that is expected and should not trigger a
  subscription upgrade or identity recreation. A code merge must not be used
  to generate cloud activity solely for a final screenshot.
- Record final credit/expiry/cost uncertainty if readable without mutations.
  Existing resources can still incur costs independently of this local package.
- The operator should review the Azure billing/closure interface and the scope
  of any deletion, access revocation or cancellation themselves. No such action
  is authorized or performed by these instructions.
- After account closure, demonstrate the archived actual evidence and fully
  offline tooling. State clearly that cloud resources are no longer live.

## Sign-off record template

```text
Repository commit / release:
Validation run and artifact manifest:
Actual cloud observations and timestamps:
Offline/synthetic demonstrations accepted:
Unexecuted live requirements and residual risks:
Subscription/credit/expiry observation and billing uncertainty:
Local VM state / consumed ledger confirmation:
Private handover location (not public credentials):
Operator acceptance / date / agreed account-closure responsibility:
```

This is an honest handover record. Do not replace an unexecuted acceptance item
with a check mark merely because the documentation or mock test exists.
