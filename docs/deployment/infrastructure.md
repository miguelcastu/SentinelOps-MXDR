# Infrastructure models and nonmutating preview

The [Bicep source](../../infrastructure/bicep/), [preview tooling](../../infrastructure/preview.py)
and [recovery procedure](recovery.md) make the existing lab reviewable as code.
They do not silently turn modeling into a broad infrastructure deployment.

## Models and preservation

`main.bicep` is subscription-scoped and uses `existing` for the named group,
West Europe workspace, Sentinel onboarding, subscription Activity export,
owned Arc machine and DCR. Workspace pricing `pergb2018`, retention 30 days
and 0.1 GB/day cap are represented as preservation invariants, never writable
template parameters. Existing declarations compile to no resource writes;
compilation alone does not check resource existence. The reference-only
diagnostic model expresses the expected workspace without inventing current
category settings or reconfiguring the export.

`ama.bicep` represents only the reviewed DCR, extension and association. Compiled
bodies must equal `ama.cloud.contract()`: local4 Warning and above, one existing
workspace, pass-through Microsoft-Syslog, fixed ownership, empty extension
settings and background automatic upgrade disabled. It creates no Arc machine,
Azure compute, custom table, Defender, Insights, DCE or other add-on. It models
possible approved recovery, not a new deployment authorization.

`disabled-rules.bicep` embeds all twelve versioned JSON files using
`loadJsonContent`. Query bodies, resource types and enabled flags are not
parameters. The sole parameter is the already-existing private AZ-DET-001 UUID;
other UUIDs are fixed in source. The parameter file reads
`SENTINELOPS_EXISTING_RULE_UUID`. The offline compiler deliberately supplies a
fictional UUID and never publishes a real target. Actual REST deployers still
enforce their existing exact-UUID pins.

## Offline comparison

```powershell
python -m infrastructure.preview
python -m infrastructure.preview --observed .local/infrastructure/snapshot.private.json --private-pin .local/infrastructure/target.private.json
```

The first command needs no credentials and produces nineteen Unknown results.
The second consumes a bounded external snapshot; it does not authenticate,
refresh it or prove its declared provenance. Actual read-back collection is a
separate operation. A file's evidence label alone cannot prove Azure produced it.

The private pin contains exactly `subscription_id` and `legacy_rule_uuid` in
canonical UUID form. Only the fixed named group/workspace is modeled, and the
tool never changes the Azure CLI account. Without a pin it uses fictional
UUIDs for local demonstrations.

The snapshot is a JSON object with exactly:

| Field | Contract |
|---|---|
| `schema` | `sentinelops-infrastructure-snapshot-1` |
| `evidence` | `synthetic`, `external-snapshot-unverified` or `actual-azure-rest-control-plane`; provenance remains unverified by this reader |
| `resources` | At most 64 objects with exactly `target`, `id`, `type`, `body` |

`target` is a fixed key from `model()`: workspace, Sentinel, diagnostic export,
Arc machine, three AMA resources or twelve AZ-DET definitions. Export complete
REST bodies/identifiers privately under ignored `.local/`; never publish raw
snapshots. The reader enforces 4 MiB input bounds, unique JSON keys/targets and
exact resource scope/type. Extra observations, wrong scopes or conflicting
duplicates stop. Comparisons cover managed fields; unrelated read-only
workspace metadata is not proposed as a configuration change. AMA's read-only
destination UUID must match independently supplied workspace metadata.

Results are Matching, Drift, Missing or Unknown and expose changed **field
paths**, not current values or IDs. Every proposed operation is `none`;
`safe_to_deploy` is always false. Missing targets never become automatic create
requests. CLI exit is nonzero for observed drift/missing resources. A default
Unknown report exits zero because model rendering succeeded, not because Azure
is healthy. `azure_requests` is zero and `arm_what_if_executed` is false.

## Destructive-change guard

`guard_changes()` reviews a bounded normalized list of `target`, `change_type`
and `after`; it never executes it. This is not a parser for every ARM what-if
response version. A separately approved adapter would need to map actual
results and preserve their provenance.

- Create/Delete/Replace/Deploy/Unsupported operations are refused.
- Workspace, Sentinel onboarding, Arc-machine or export modifications are
  refused, including pricing, retention, cap and destination changes.
- Modify is reviewable only at an already-approved exact AMA/rule target with
  a body identical to its reviewed contract.
- Enabled rules, arbitrary KQL, extension commands, extra destinations,
  unknown/duplicate targets and additional resource types are refused.
- A successful local review still does not grant permission to deploy.

The package has no apply flag, Azure client/token acquisition, deletion path,
subscription-selection command or deploy command.

## Genuine Bicep compilation and CI

The compiler is official **Azure/bicep 0.48.1**. Windows/Linux x64 release
digests are pinned in [tools.lock.json](../../infrastructure/bicep/tools.lock.json).
Download the exact official release artifact, verify its SHA-256, keep it in
ignored `.local/tools/`, then run:

```powershell
python -m infrastructure.preview --bicep .local/tools/bicep-v0.48.1.exe
```

The wrapper rechecks the digest, compiles four templates with `--no-restore`
and one parameter file, and rejects compiler/linter diagnostics. A finite
resolver checks compiled AMA and all twelve disabled rule contracts; unknown
expressions fail closed. It verifies unique rule targets and zero writable
foundation/export resources. Generated output is private local evidence, not
a platform deployment. Unit tests run the compiler when the locked binary is
available and explicitly skip those compiler tests otherwise; the explicit
compile step reproduces the recorded result.

PR validation has no Azure login/OIDC permission. Existing protected main-only
REST workflows use one reused identity, immutable trust and exact-resource
roles. The [actual RBAC audit](../../evidence/local-linux-ama/preservation.sanitized.json)
does not grant group/subscription ARM deployment permission. Their successful
actual REST runs establish the authorized update path, not deployment of these
Bicep files. Do not grant Contributor/Owner or run ARM what-if to manufacture
evidence. Any new ARM workflow needs its own scope, permissions, cost review,
actual what-if and approval.

Microsoft documents [existing-resource semantics](https://learn.microsoft.com/azure/azure-resource-manager/bicep/existing-resource),
[official compiler installation](https://learn.microsoft.com/azure/azure-resource-manager/bicep/install)
and [monitoring scopes](https://learn.microsoft.com/azure/azure-resource-manager/bicep/scenarios-monitoring).
These sources explain the implementation; [Phase 6 validation](../validation/phase-6.md)
records what this lab actually executed.
