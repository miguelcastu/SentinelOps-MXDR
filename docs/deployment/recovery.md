# Recovery and account-close handover

This procedure recovers **configuration and local tooling**, not deleted
Log Analytics telemetry. Git is not a backup of ingested logs. No command
here deletes Azure resources, restarts collection or changes subscription.
Recovery starts with an offline preview and never auto-reconciles differences.

## Recovery material and limits

| Item | Available material | Limit |
|---|---|---|
| Detection JSON/KQL | Git history, fixed catalog and validators | Does not restore past alerts, incidents or runtime |
| AMA contract | Python, Bicep representation and dated actual evidence | Guest disk/key and Arc identity files are private assets |
| Topology | Existing-only Bicep and preservation invariants | Does not recreate the workspace or subscription |
| Synthetic pipeline | Deterministic inputs, risk/case engines and tests | Synthetic output is not real telemetry |
| Cloud state | Dated sanitized read-backs | Can become stale/unavailable after closure |
| Private identifiers/credentials | Operator-controlled private backup | Cannot be reconstructed from public Git |

A clean clone can replay offline demonstrations with Python 3.12+. No production
RTO/RPO or disaster failover is measured. Cloud restoration and any data backup
need separate validation; historical evidence does not imply service continuity.

## Recovery sequence

1. **Freeze new changes.** Keep the local Linux guest stopped. Preserve completed
   bootstrap/pilot ledgers, private baselines and failure codes. Do not reset a
   ledger to force a replay.
2. **Check eligibility.** If the subscription expired, is Disabled, lacks credit
   or is being closed, do not deploy/upgrade. Continue repository handover and
   local verification only; mark cloud state unavailable/historical.
3. **Validate source.** Use a feature branch; run required tests/validators and
   `python -m infrastructure.preview`. Do not run an old administrative setup
   because it exists: older scripts intentionally reject new privilege sets.
4. **Inspect only if authorized.** Compare the account with the private pin
   before requesting exact resources. Use legitimate MFA and approved read-only
   paths; keep full responses private. Never change tenant/subscription, use
   Cloud Shell, upgrade trial or widen roles to bypass a failure.
5. **Classify first.** Authorization/MFA failure is not evidence of absence.
   A transient agent-provider 404 is not permission to create a duplicate.
   Stopped Arc is expected maintenance. Missing foundation infrastructure needs
   a separately approved restoration plan, not the detection deployer.
6. **Preview the smallest fix.** An existing disabled rule must use its current
   UUID and reviewed contract. AMA must retain the exact owned machine and DCR
   destination. Reject deletions, extra destinations, broad assignments,
   activation and billing/retention/cap/export changes. Run local fault cases.
7. **Use protected Git/OIDC.** Review the source PR, require final-head `offline`
   success, normal merge and the existing main-only fixed REST workflow.
   Do not reuse the completed personal initialization exception.
8. **Verify persisted state.** Record actual REST comparison, source/workflow
   SHA, unaffected settings and narrow permissions. Ambiguity means stop, not
   escalation. No new query, upload or guest boot is implied by a config fix.

## Rollback and cold restore

Rollback is a new reviewed commit returning to a previously approved contract,
not force push, Git history rewrite or resource deletion. If an old contract
differs from today's approved fingerprint, revisit scope before dispatching.
Keep intended rules disabled; do not disable the Activity export to roll back
a detection. Missing resources do not authorize automatic recreation.

REST upsert and ARM deployment require different permissions. Current recovery
uses approved exact-resource REST workflows. Bicep is compiler-validated;
no ARM deployment/what-if access is inferred. Never use complete-mode deployment
or add a group-level writer for convenience. Validate any separately approved
restore against a fresh baseline before touching collection or billing.

## Private backup and reviewer handover

Back up the guest disk/configuration privately only if needed. Treat SSH keys,
Arc machine identity files, known_hosts, Azure CLI and Git credential stores as
secrets; keep backups encrypted and access restricted. Public Git excludes
`.local/`, raw logs, identifiers and generated real-target templates. Reviewers
need none of those private assets to inspect code and reproduce synthetic
reports. Use the [portfolio walkthrough](../portfolio/) and [customer handover](../../customer/atlas-financial/).
Do not present a historical screenshot as a promise of current availability.

## Closing Azure

Account closure remains the operator's action; code does not close the account
or delete resources. Keep the guest off and preserve sanitized evidence/private
billing records. Subscription policy/export objects are distinct from the group;
removing a group alone is not a complete teardown method. Review actual billing
and ongoing services before closure. Closed credit balances can lag usage;
budget alerts and daily caps are not universal monetary limits. Never upgrade,
remove the spending limit or switch subscription to continue a demonstration.
After closure retain the offline replay and label cloud evidence historical;
no service availability, response or retention commitment survives shutdown.
