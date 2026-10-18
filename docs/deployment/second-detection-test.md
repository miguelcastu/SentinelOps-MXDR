# One-time restricted connection and second-detection deployment

The operator requested a second detection on 18 October 2026. PR #1 is merged, but the GitHub environment still has no Azure identifiers. The agent must not use the personal Azure/Owner session or grant roles autonomously, as required by the original task and [AGENTS.md](../../AGENTS.md). One administrative step therefore belongs to the operator.

## Prepared test

AZ-DET-002 observes successful Azure RBAC role-assignment creation in the existing AzureActivity data. The rule and incident creation stay disabled. The agent has pinned the existing subscription and tenant privately in `.local/azure-target.json` (ignored by Git). No subscription identifier is included in public source. The bootstrap refuses a changed account context and never selects or upgrades a subscription.

## Operator action

Review [scripts/bootstrap_oidc.py](../../scripts/bootstrap_oidc.py), then execute this **yourself** in the repository's PowerShell terminal:

```powershell
uv run --python 3.12 --with pynacl==1.6.2 --no-project python -m scripts.bootstrap_oidc --apply
```

Without `--apply`, the same command only previews the plan and checks cached local account metadata. The agent has run that preview, not the administrative apply. Azure CLI, Git authentication and `uv` were verified on this machine. PyNaCl is a temporary local dependency for GitHub's public-key secret encryption; the normal validation/deployment tooling has no Python package dependencies. Its sealed-box encryption was checked with synthetic input. Do not send identifier or credential values through chat.

The apply step:

1. Checks the private subscription pin, the existing West Europe workspace, public GitHub repository, enforced main PR protection and main-only environment policy.
2. Creates/reuses `id-sentinelops-rule002-ci`, with no paid compute. [Microsoft documents managed identities at no extra cost](https://learn.microsoft.com/en-us/entra/identity/managed-identities-azure-resources/overview).
3. Creates/reuses one custom role with only analytics-rule read/write and workspace metadata read, assigned to the existing workspace. Unexpected existing permissions or trust settings stop the process instead of being overwritten.
4. Creates/reuses the exact GitHub environment OIDC trust. No client password is generated.
5. Encrypts and sets `AZURE_ADDITIONAL_CLIENT_ID`, `AZURE_TENANT_ID` and `AZURE_SUBSCRIPTION_ID` in `sentinel-lab`, using the existing Git credential without printing or saving it.
6. Sets only `SENTINEL_AZ_DET_002_APPROVED=true`. Approval flags for AZ-DET-001 and live queries remain unchanged.

It does **not** deploy a rule, run a log query, create connectors, modify diagnostics, install Defender plans or change retention, daily caps, budgets, pricing or billing. Partial setup can be rerun after resolving its reported error; it does not delete or roll back existing resources. If login has expired, the operator must sign in personally and preserve the pinned subscription. Do not switch subscriptions to get past a failed check.

## Permission scope and review boundary

Creating a new rule requires write access before its resource exists. This separate identity therefore has `Microsoft.SecurityInsights/alertRules/read`, `Microsoft.SecurityInsights/alertRules/write` and `Microsoft.OperationalInsights/workspaces/read` **at the existing workspace**, rather than the original identity's exact-rule update scope. It has no delete, log-query, connector, deployment, billing or role-management permission.

RBAC still permits writing any analytics rule in that workspace and cannot enforce `enabled=false`. Reviewed main-only workflow code supplies the fixed UUID, body, disabled-state and duplicate checks. The separate client secret name prevents changing AZ-DET-001's identity. This is broader rule-write scope than the first pipeline; review it before applying. It is not a technical guarantee of zero ongoing Azure spend.

## Merge, deploy and verify

After successful setup, review and merge the second-detection PR yourself. The main-only **Deploy Additional Disabled Detection** workflow runs on the new detection files. It validates both detections/tests, checks prerequisites, authenticates with the separate OIDC identity, checks the existing workspace/rule inventory, creates or updates only AZ-DET-002, and GETs the exact resource to compare every managed property.

If the PR was merged before configuration, manually run that workflow on `main`, or ask the agent to dispatch it after setup. Do not bypass branch/environment protection or enable the rule. Report success only when the actual workflow and final REST verification succeed. Capture the Actions run link as evidence; synthetic tests and a successful bootstrap do not prove the rule was deployed.
