# Detection-as-code deployment runbook

This pipeline updates **one existing disabled rule** in the existing subscription. Do not change the subscription, billing plan or workspace. Approximately 175 EUR remaining credit was reported by the operator; its actual balance, currency and expiry have not been independently verified.

## Local checks (no Azure calls)

```powershell
python -m scripts.validate_detection
python -m unittest discover -s tests -v
```

Python 3.12+ and the standard library are sufficient. There are no runtime Python dependencies. Offline CI uses a standard `ubuntu-latest` runner and has no Azure secrets or OIDC permission. [Standard hosted runners are free for public repositories](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#choosing-github-hosted-runners). All jobs refuse to run if the repository becomes private, so a future visibility change requires a fresh cost decision. Workflows do not upload artifacts or schedule recurring health queries.

## Prerequisites the operator must complete

The agent must not use the personal Azure user/Owner session to create an identity or grant roles. Missing configuration blocks Azure deployment; it does not block local development or opening the PR. Do the following administrative setup yourself, using the Azure portal or your own reviewed commands, against the **currently selected existing subscription**.

1. In Azure Portal, confirm the current subscription matches the lab and review Cost Management credit, expiry and existing usage. Do not upgrade or select another subscription.
2. Confirm `rg-sentinelops-mxdr` / `law-sentinelops-mxdr-euw` already exists in West Europe, Sentinel is already enabled, and Azure Activity is already onboarded. Do not provision replacements.
3. Open Analytics and find exactly one rule named `AZ-DET-001 - Azure Diagnostic Settings Modified`. Record its existing UUID and resource ID privately. Confirm its kind is Scheduled and it is already disabled. If absent, duplicated or enabled, stop and resolve with the operator; this pipeline cannot create a replacement or choose a target for you.
4. Confirm Microsoft Sentinel Repositories or another automation system does not also manage that rule.
5. Inspect for an existing dedicated managed identity `id-sentinelops-ci`. If none exists, the operator must explicitly create it in the existing group; identity creation is an administrative prerequisite, not an autonomous agent action. Do not assign Owner, Contributor or Sentinel Contributor.
6. Have an administrator grant the narrow permissions described below and inspect all inherited assignments for that principal. Azure permissions add together; a narrow custom role does not cancel a broader inherited role.
7. Add the managed identity's OIDC federated credential with the exact settings below.
8. In GitHub, configure the protected `sentinel-lab` environment and fill its secrets/variables. Never post their values into issues, PRs or chat.

An administrator may inspect the existing rule with this **read-only** request in their own terminal. It does not select a subscription or make changes:

```powershell
$workspaceId = az monitor log-analytics workspace show `
  --resource-group rg-sentinelops-mxdr `
  --workspace-name law-sentinelops-mxdr-euw --query id -o tsv
$url = "https://management.azure.com$workspaceId/providers/Microsoft.SecurityInsights/alertRules?api-version=2025-09-01"
$rules = (az rest --method get --url $url | ConvertFrom-Json).value
$matches = @($rules | Where-Object {
  $_.properties.displayName -eq 'AZ-DET-001 - Azure Diagnostic Settings Modified'
})
if ($matches.Count -ne 1) { throw 'Expected exactly one existing rule; do not guess or create a duplicate.' }
if ($matches[0].kind -ne 'Scheduled' -or $matches[0].properties.enabled -ne $false) {
  throw 'The existing target must already be a disabled Scheduled rule.'
}
# Inspect $matches[0].name and .id privately; do not paste them into public evidence.
```

## Least-privilege Azure boundary

Use separate custom role assignments so rule-write permissions do not span all workspace rules:

| Assignment scope | Allowed Actions | Purpose |
|---|---|---|
| Exact existing rule resource ID | `Microsoft.SecurityInsights/alertRules/read`, `Microsoft.SecurityInsights/alertRules/write` | Read/update AZ-DET-001 only |
| Exact workspace resource ID | `Microsoft.OperationalInsights/workspaces/read` | Verify existing workspace ID/location |
| Exact workspace resource ID, optional for live checks | `Microsoft.OperationalInsights/workspaces/query/read`, `Microsoft.OperationalInsights/workspaces/query/AzureActivity/read` | Run fixed AzureActivity queries |

Define custom roles with `NotActions`, `DataActions` and `NotDataActions` empty, and `AssignableScopes` limited to the existing resource group. Assign the actions only at the scopes above. No delete, shared-key, infrastructure-write, role-assignment or billing permissions are required. This is an intentional restriction compared with the broader workspace-wide deployer and Log Analytics Reader roles in the initial proposal.

Microsoft documents [custom Sentinel roles](https://learn.microsoft.com/en-us/azure/sentinel/roles) and the [table-specific query permissions](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/manage-table-access#configure-table-level-access-legacy-method). That table-specific Actions method remains documented but is now labeled legacy. Environments using newer granular/protected-table RBAC may require an administrator to configure equivalent AzureActivity-only data access. Do not automatically fall back to a broad Reader role or change the workspace's access model.

RBAC cannot constrain `alertRules/write` to `enabled=false`, nor distinguish create from update on that same resource path. The pipeline's exact-ID, existing-resource, etag and disabled-state checks supplement RBAC. Environment protection and reviewed workflow changes are part of the trust boundary. Never describe AGENTS.md or a budget as a spending lock.

## OIDC trust and GitHub settings

| Federated credential field | Exact value |
|---|---|
| Issuer | `https://token.actions.githubusercontent.com` |
| Subject | `repo:miguelcastu/SentinelOps-MXDR:environment:sentinel-lab` |
| Audience | `api://AzureADTokenExchange` |

See [Azure login with OIDC](https://learn.microsoft.com/en-us/azure/developer/github/connect-from-azure-openid-connect) and [GitHub OIDC claims](https://docs.github.com/en/actions/reference/security/oidc). Environment credentials are bound to the environment subject, so **restrict that environment to the `main` branch**. Workflow branch checks alone are insufficient: an untrusted branch must not be allowed to obtain the same federated token.

In repository Settings → Environments → `sentinel-lab`, allow only branch `main`, no tag patterns. Protect main with pull requests and disallow force pushes. Review changes to the workflows, validators and schema as carefully as the detection itself.

| Environment secret | Source |
|---|---|
| `AZURE_CLIENT_ID` | Dedicated managed identity's client/application ID |
| `AZURE_TENANT_ID` | Existing subscription's tenant |
| `AZURE_SUBSCRIPTION_ID` | **The same existing subscription**, never a replacement |

| Environment variable | Initial value / gate |
|---|---|
| `SENTINEL_RULE_ID` | Existing rule UUID, only after unique-target verification |
| `SENTINEL_EXCLUSIVE_RULE_OWNER` | `false` until the operator confirms no competing deployment system |
| `SENTINEL_DEPLOYMENT_APPROVED` | `false` until identity, RBAC, same-subscription and target checks are reviewed |
| `SENTINEL_LIVE_VALIDATION_APPROVED` | `false`; optional, only after a query-cost/access review |

The three approval flags require the literal string `true`. Identifiers are not passwords, but storing authentication IDs as environment secrets keeps them out of public code and normal workflow output. Do not add client secrets; OIDC does not need one. `azure/login` authenticates to the configured existing subscription; scripts stop on mismatched tenant/subscription/client and never run a subscription-switch command.

## First controlled deployment

1. Review and approve the implementation PR. Keep approval flags false until all prerequisites are ready.
2. Merge the approved PR into `main` yourself. The agent does not merge on your behalf.
3. After prerequisite review, set the exclusive-owner and deployment-approved flags to `true`, then run **Deploy Sentinel Detection** on `main` (or let a later approved detection change trigger it).
4. Validation and prerequisite checks run before OIDC login. An error stops the job, without creating infrastructure or expanding permissions.
5. The deployer verifies the dedicated service principal, expected subscription/tenant, exact workspace/location and existing rule's type, name, disabled state and etag.
6. It sends one conditional PUT with the observed etag and `If-Match`, then GETs the same resource and compares all managed properties. It never retries a conflict with a new etag.
7. Record the successful Actions run link, commit and sanitized REST-verification result in the validation record. An offline pass is not evidence of cloud deployment.

The [Sentinel endpoint](https://learn.microsoft.com/en-us/rest/api/securityinsights/alert-rules/create-or-update?view=rest-securityinsights-2025-09-01) is an upsert API. Service-side concurrency behavior has not yet been verified in this lab; keep the target under exclusive ownership and do not delete/recreate it during deployment. The code uses one configured UUID and never generates a new one. A missing GET stops before PUT. If strict server-enforced update-only semantics cannot be confirmed, keep the deployment gate false pending review.

## Optional read-only live KQL validation

Run **Read-only KQL Validation** manually on `main`, after enabling its approval variable and checking its confirmation box. It has no scheduled or PR trigger and accepts no arbitrary query input. After an existing-workspace metadata GET, it sends exactly two fixed query requests: a one-hour count-only AzureActivity health check and actual detection logic over in-memory synthetic data. It uses the [documented Logs API endpoint and token audience](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/api/request-format). It never generates activity events, ingests fixtures, exports data, restores logs or returns caller/resource rows. The same dedicated identity is used; this workflow's code performs only read/query operations, while the principal also retains its single-rule write permission. A separate query-only identity is a future hardening option.

Microsoft's [query pricing documentation](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/cost-logs) distinguishes Analytics queries from Basic/Auxiliary and retention-related scans; the [AzureActivity table reference](https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/azureactivity) currently lists no Basic/Auxiliary support. Confirm the existing environment before using the opt-in; this task does not need a chargeable query. Do not enable query auditing or other features just to validate this pipeline.

The query wrapper captures responses privately, rejects partial errors or unexpected columns, and prints only nonnegative integer aggregates. No raw Azure error response is printed because it may contain identifiers or query text. Zero activity is a valid lab outcome and does not prove connector health.
