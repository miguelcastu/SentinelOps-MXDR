# Existing-identity Detection-as-Code setup

This supersedes the original operator-only proposal. The operator authorized initial Azure/GitHub administration on 18 October 2026. Routine deployment uses GitHub OIDC; the personal MFA account is confined to setup and verification. The existing subscription and billing plan remain pinned and unchanged.

## Reproducible setup

Existing resources: rg-sentinelops-mxdr, law-sentinelops-mxdr-euw in West Europe, Sentinel, disabled AZ-DET-001 and **id-sentinelops-ci**. The script refuses ambiguous/missing targets; it never creates a replacement identity or rule. Ignored .local/azure-target.json pins the original subscription and tenant. Never publish its values or select another subscription to pass a check.

```powershell
# Preview, without cloud changes:
uv run --python 3.12 --with pynacl==1.6.2 --no-project python -m scripts.bootstrap_oidc
# Explicitly authorized administrative setup after MFA:
uv run --python 3.12 --with pynacl==1.6.2 --no-project python -m scripts.bootstrap_oidc --apply
```

[bootstrap.ps1](../../scripts/bootstrap.ps1) wraps those commands; -Apply enables administration. PyNaCl 1.6.2 is a temporary local dependency for sealed-box encryption. Normal CI/deployment uses only the standard library. This resolves the earlier dependency failure without installing packages in Azure or storing credentials.

## MFA and resource scope

Azure returned HTTP 401 RequestDisallowedByAzure on a required role-definition write, with an official WWW-Authenticate challenge for context p1. Supported interactive Azure CLI login used that challenge, the pinned tenant/subscription and scope https://management.core.windows.net//.default; the operator completed MFA.

The intended ARM core token then contained mfa/p1 and Azure accepted the administrative PUT with HTTP 201. A separately cached management.azure.com token still lacked those claims; inspecting that alias alone incorrectly suggested reauthentication failed. Never print access tokens, extract browser credentials, weaken Conditional Access or use Cloud Shell. Follow the actual challenge and verify the intended resource token plus service response. See [Microsoft MFA troubleshooting](https://learn.microsoft.com/en-us/cli/azure/use-azure-cli-successfully-troubleshooting#troubleshooting-multifactor-authentication-mfa).

## Least privilege

| Role | Actions | Assignment scope |
|---|---|---|
| SentinelOps Existing Analytics Rule Deployer | Microsoft.SecurityInsights/alertRules/read and /write | Exact AZ-DET-001 and AZ-DET-002 resources, separate assignments |
| SentinelOps Workspace Metadata Reader | Microsoft.OperationalInsights/workspaces/read | Exact existing workspace |
| SentinelOps Analytics Rule Inventory Reader | Microsoft.SecurityInsights/alertRules/read | Exact existing workspace, duplicate checks for AZ-DET-002 |

Custom-role assignable scopes are restricted to the existing group. NotActions/DataActions/NotDataActions are empty. No wildcard, delete, shared-key, infrastructure, billing, query or RBAC-management action is granted. Definitions must match the approved actions; name-based discovery reuses roles created by legacy CLI versions; new roles and assignments use deterministic REST IDs. Complete inventories prevent duplicates. Unexpected inherited roles or trusts stop setup. Optional query access is not granted without a required bounded validation.

Permissions add together: audit definitions and applicable assignments. Do not test a denial by trying paid resource creation or changing pricing. The allowed-action set and scopes supply the boundary; actual CI verifies permitted operations. Diagnose service errors before adding permissions.

## GitHub OIDC

The existing sentinel-lab environment allows only branch main, no tags. Main requires a PR, successful offline check, current-branch validation and resolved conversations. Admin enforcement is on; force pushes/deletion are prohibited. Public-repository standard runners are free; workflows refuse private repositories.

| Trust field | Actual value |
|---|---|
| Issuer | https://token.actions.githubusercontent.com |
| Audience | api://AzureADTokenExchange |
| Subject | repo:miguelcastu@98903292/SentinelOps-MXDR@1417963827:environment:sentinel-lab |

New repositories use [immutable subjects](https://docs.github.com/en/actions/reference/security/oidc#immutable-subject-claims). Bootstrap reads sub_claim_prefix from the authenticated repository OIDC API and validates it against repository metadata. The first workflow failed with AADSTS700213 because the proposal used a legacy name-only subject. The existing credential was corrected in place; no extra identity/trust was added. Custom or unrelated subjects are not guessed or overwritten.

Secrets: AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_SUBSCRIPTION_ID. Values are encrypted in memory with GitHub's environment public key and the existing Git credential. There is no client password. Variables pin the existing rule UUID and deployment/exclusive-owner approval. The live-query flag stays false until separately reviewed.

## Deployment and evidence

PRs validate offline without OIDC or Azure environment credentials. Approved main changes deploy with the restricted identity. The deployer verifies tenant/client/subscription, workspace/location, exact existing rule/type/name/disabled state and etag; it conditionally PUTs that resource and compares managed properties after GET. Sanitized Azure error codes remain visible; raw identities/telemetry do not. The API is an upsert endpoint: do not concurrently delete/recreate targets or assume unverified conditional-header semantics.

The manual Check Sentinel Configuration Drift workflow compares source using GET only, with no recurring schedule or log query. Within-run identical rows are removed by distinct; cross-run overlap remains a limitation while AZ-DET-001 stays disabled.

Original configuration was saved privately and as [sanitized evidence](../validation/AZ-DET-001-original.sanitized.json). It had a 30-minute query period with a 24-hour predicate, T1562 and a Caller/Account mapping. Source aligns the predicate/period to one hour, preserves the existing parent technique T1562 (subtechnique T1562.008 is documented separately) and avoids assuming callers are human accounts. The rule and incident creation remain disabled.

Both disabled deployments and the clean manual drift check are now verified. Actual Actions and Azure GET evidence, not bootstrap/login/tests alone, is required for success. Preserve workspace, connector resources and diagnostic settings. See the [validation record](../validation/platform-setup.md).

For a fresh additional-rule setup, append --include-additional (or -IncludeAdditional with the PowerShell wrapper). Azure accepted the exact UUID assignment before creation, so no broad write grant is required. Existing additional-rule assignments are also recognized on ordinary reruns.
