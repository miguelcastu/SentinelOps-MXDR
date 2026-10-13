# Runbook: onboard Azure Activity into Microsoft Sentinel

**Client:** Atlas Financial (*fictional*)  
**Source:** Azure subscription's management-plane Activity Log  
**Target:** `law-sentinelops-mxdr-euw` / `AzureActivity`

## Procedure

1. In Sentinel Content Hub, install the **Azure Activity** solution.
2. Open the native connector and launch the Azure Policy assignment wizard.
3. Scope the built-in **Configure Azure Activity logs to stream to specified Log Analytics workspace** policy at the subscription level, not only at the resource-group level.
4. Verify `logAnalytics` points to the target workspace; `effect=DeployIfNotExists`; `logsEnabled=True`.
5. Allow Azure Policy evaluation. If the existing subscription lacks a diagnostic configuration, find the policy under **Remediation**.
6. Create a remediation task for the non-compliant resource. In this lab the task subsequently reported **Complete, 1/1 resources remediated**.
7. Navigate to subscription → Activity Log → **Diagnostic settings** and verify an export named `subscriptionToLa` targeting the workspace. Do not create an additional duplicate export.
8. Wait for export/ingestion, generate harmless management activity if necessary, then query the `AzureActivity` table from the **correct workspace**.

## Minimal validation KQL

```kusto
AzureActivity
| where TimeGenerated > ago(24h)
| summarize TotalEvents=count(), FirstEvent=min(TimeGenerated), LastEvent=max(TimeGenerated), UniqueCallers=dcount(Caller)
```

A query returning real records establishes end-to-end delivery but not comprehensive category coverage or permanent connector health.

## Troubleshooting method

**Source exists → policy scope and parameters → remediation status → diagnostic setting → workspace/table → time range and ingestion cap.** If anything fails, inspect the specific operation and permissions before duplicating exporters. See [case study](../troubleshooting/azure-policy-remediation.md).
