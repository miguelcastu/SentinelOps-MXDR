# Architecture — Azure foundation and ingestion

## Environment

| Component | Lab value |
|---|---|
| Logical customer | Atlas Financial (fictional) |
| Resource group | `rg-sentinelops-mxdr` |
| Resource group metadata region | Spain Central |
| Workspace | `law-sentinelops-mxdr-euw` |
| Workspace and Sentinel location | West Europe |
| Source | Azure Activity (subscription management plane) |
| Output table | `AzureActivity` |
| Export mechanism | Subscription diagnostic settings |

The resource-group metadata location is distinct from the physical region of the Log Analytics workspace. The lab was migrated to a compatible Sentinel workspace region rather than attempting to change the existing workspace's location.

## Responsibilities

- **Azure Resource Manager:** management operations that produce activity events.
- **Azure Activity Log:** native subscription-level administrative event log. Not a Defender endpoint sensor and not Entra ID sign-in logs.
- **Azure Policy:** policy assigned at subscription scope with `DeployIfNotExists` and `logsEnabled=True`, targeting a specific Log Analytics workspace.
- **Remediation:** applies missing diagnostic settings to a pre-existing non-compliant subscription.
- **Diagnostic settings:** native Azure Monitor export configuration; observed name `subscriptionToLa`.
- **Log Analytics:** destination and query engine for `AzureActivity` records.
- **Microsoft Sentinel:** security analytics, detection and hunting over data in the workspace.

## Engineering trade-offs

| Decision | Why | Limitation |
|---|---|---|
| Native Azure Activity as first log source | Quick, real operational telemetry without VM agents | Does not cover sign-ins, endpoints or network flows |
| Policy-driven diagnostic settings | Standardized, auditable configuration | Existing subscriptions may require remediation; identity permissions matter |
| Single West Europe workspace | Simple compatible lab deployment | Does not demonstrate resilience or multi-tenancy |
| KQL query validation | Proves destination receives events | Does not prove every source category is ingested |
| Budget alerts and low-volume workload | Keeps lab spending observable | No guaranteed upper bound on Azure charges |

Next phases will add detection-as-code, data health checks, automation and reproducible Bicep deployments.
