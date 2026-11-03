# Infrastructure as code and safe recovery

The manually provisioned lab now has real, compiler-validated [Bicep models](bicep/),
a zero-network [fixed-contract preview](preview.py), parameter handling and a
[recovery runbook](../docs/deployment/recovery.md).

| Model | What is represented | Write boundary |
|---|---|---|
| `bicep/main.bicep` | Existing group, workspace, Sentinel onboarding, subscription export, Arc machine and DCR | Existing references only; zero resource writes |
| `bicep/diagnostic-export.bicep` | Existing subscription export and expected workspace destination | No category/destination/retention changes |
| `bicep/ama.bicep` | Fixed local4 Warning DCR, AMA extension and association | Exact current Python contract; recovery representation |
| `bicep/disabled-rules.bicep` | All twelve reviewed disabled analytics definitions | Source JSON embedded at compile time; no query/body parameter |
| `bicep/disabled-rules.bicepparam` | Existing AZ-DET-001 UUID from a private environment variable | No real identifier committed |

```powershell
python -m infrastructure.preview
# Optional genuine compile with an already-downloaded hash-pinned compiler:
python -m infrastructure.preview --bicep .local/tools/bicep-v0.48.1.exe
```

The default report is **Unknown** for nineteen modeled targets because no live
snapshot is fetched. It writes `.local/infrastructure/preview.json`, prints
sanitized states/field paths, and performs no Azure request. Missing resources
never become create proposals. It is not Azure ARM what-if.

The optional step genuinely compiles four templates and one parameter file,
then checks the three AMA resources and twelve rules against the existing
Python/JSON contracts. The official compiler is pinned in [tools.lock.json](bicep/tools.lock.json).
Binaries/generated templates remain ignored; there is no automatic installer
or cloud deployer. See [design and change gates](../docs/deployment/infrastructure.md)
and [actual validation scope](../docs/validation/phase-6.md).

Existing protected main-only OIDC **REST workflows** remain the deployment
path for approved fixed resources. Exact-resource permissions do not grant
group/subscription ARM deployment or what-if access. No platform Bicep
deployment or ARM what-if is claimed. A new deployment workflow would need
separate scope, permissions, pricing/preservation review and approval.

[ingestion/](ingestion/) remains the separate synthetic-authentication Direct
DCR/custom-table REST proposal, not deployed by these models and distinct from
the completed local Linux AMA pilot.
