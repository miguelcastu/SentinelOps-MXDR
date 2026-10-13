# SentinelOps MXDR

**Microsoft Sentinel platform-engineering lab**

> **v0.1 — verified foundation and Azure Activity onboarding (13 October 2026).** Detection-as-code, IaC and SOAR are planned, not yet implemented.

This technical lab covers SIEM platform deployment, source onboarding, troubleshooting, KQL investigations and ingestion-health validation. The documented environment is a lab, not a production deployment.

## Proven deliverables

| Engineering capability | Evidence |
|---|---|
| Microsoft Sentinel on Log Analytics (West Europe) | [Azure resource inventory](evidence/01-azure-resources.png) |
| Azure Activity solution and connector configured | [Connector inventory](evidence/02-azure-activity-connector.png) |
| Azure Policy `DeployIfNotExists` assigned | [Policy parameters](evidence/03-azure-policy-assignment.png) |
| Existing subscription remediated: **1/1 resources** | [Remediation result](evidence/04-remediation-complete.png) |
| Subscription-level diagnostic export to workspace | [Diagnostic setting](evidence/05-diagnostic-settings.png) |
| Activity events queryable with KQL | [Query result](evidence/06-kql-ingestion-summary.png) |
| Operations analysis and estimated ingestion latency | [Operations](evidence/07-kql-administrative-operations.png) · [Latency](evidence/08-kql-ingestion-latency.png) |

**Observed snapshot:** 9 records, 3 distinct `Caller` values; mean estimated ingestion delay 7.89 min, maximum 9 min. These are *point-in-time lab observations*, **not** production performance targets or SLAs. The connector inventory itself shows a neutral Azure Activity status, so correctness is established through the diagnostic export and actual `AzureActivity` table results, not by assuming the connector UI is green.

## Data flow

```mermaid
flowchart TD
    ARM[Azure Resource Manager
Management actions] --> SRC[Azure Activity Log
Log source]
    POL[Azure Policy
DeployIfNotExists] --> REM[Remediation task
Existing subscription]
    REM --> DIA[Subscription diagnostic settings]
    SRC --> DIA
    DIA --> LAW[Log Analytics
AzureActivity table]
    LAW --> SENT[Microsoft Sentinel
KQL / hunting / security analytics]
```

Azure Policy **governs and deploys configuration**, rather than forwarding event payloads itself. Diagnostic settings export Azure Activity to Log Analytics. Sentinel queries the ingested data. Learn more in the [architecture overview](docs/architecture/overview.md).

## Getting started

1. Follow the [manual deployment record](docs/deployment/azure-sentinel-setup.md).
2. Review the [Azure Activity onboarding runbook](docs/onboarding/azure-activity.md).
3. Read the [Azure Policy remediation incident](docs/troubleshooting/azure-policy-remediation.md).
4. Run the reusable [KQL queries](hunting/) against a workspace containing `AzureActivity`.
5. Review [validation evidence](docs/validation/first-ingestion.md) and the [roadmap](docs/roadmap.md).

## Project organization

```text
docs/         Architecture, onboarding, deployment, validation, troubleshooting
hunting/      Reusable KQL queries
evidence/     Sanitized Azure screenshots
infrastructure/  Reserved for future Bicep implementation
tests/        Lightweight offline project validation
```

## Costs and privacy

Azure budgets are alerts, **not hard spending limits**. Promotional credit and product trials are subject to eligibility and expiration. Verify charges, Log Analytics ingestion, retention and workspace caps in your own subscription. Do not include secrets, tenant/subscription IDs, email identities or unredacted event logs. See [evidence guidelines](docs/evidence-handling.md).

## Status / roadmap

- ✅ Azure foundation, Sentinel, Content Hub, Azure Policy remediation, working Azure Activity ingestion, KQL validation.
- ⬜ Detection engineering, scheduled analytics rules, entity mapping, MITRE ATT&CK, alert investigations.
- ⬜ Connector health, telemetry coverage, ingestion baseline and troubleshooting.
- ⬜ Logic Apps / Python automation, idempotency, failures and cost management.
- ⬜ Bicep Infrastructure as Code and automated deployments.
- ⬜ Operational runbooks, service KPIs and handover.
