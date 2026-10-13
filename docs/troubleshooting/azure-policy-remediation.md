# Troubleshooting case: Azure Activity connector configured, but logs not exported

**Date:** 13 October 2026  
**Type:** MXDR platform integration issue  
**Result:** remediation completed, diagnostic setting deployed, events ingested.

## Symptom and impact

The Azure Activity Content Hub solution and Policy assignment were present, but **no subscription diagnostic setting existed**. Activity records could be seen in the subscription's native log, yet there was no demonstrated delivery into the SIEM workspace.

## Investigation and resolution

1. Validated native subscription Activity Log events, including policy/role-assignment operations.
2. Checked the assigned built-in policy. Parameters were `DeployIfNotExists` and `logsEnabled=True` with a workspace target.
3. Found **0 remediation tasks**, despite a non-compliant resource appearing in policy compliance.
4. Created a remediation task scoped to the pre-existing subscription.
5. Observed completion: **1 out of 1 resources corrected**.
6. Rechecked subscription diagnostic settings; export `subscriptionToLa` now targeted `law-sentinelops-mxdr-euw`.
7. Queried `AzureActivity` via KQL and observed **9 real events** in the validation window.

The operations query also recorded a remediation-related **Failure** event. Its particular cause cannot be established from these screenshots, and it should not be attributed to RBAC or a platform defect without further evidence. Final successful remediation is separately documented.

## Root cause (observed)

Missing subscription diagnostic settings and a not-yet-run correction step for an existing non-compliant subscription. `DeployIfNotExists` is a governance/deployment effect, not a live event-forwarding service.

## Lessons

Never infer working telemetry from the presence of a connector package. Validate **producer → configuration → destination → query**, record intermediate errors, and avoid duplicate ingestion routes.

Evidence: [Policy assignment](../../evidence/03-azure-policy-assignment.png) · [Completed remediation](../../evidence/04-remediation-complete.png) · [Diagnostic export](../../evidence/05-diagnostic-settings.png) · [KQL operations](../../evidence/07-kql-administrative-operations.png).
