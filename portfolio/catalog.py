"""Fixed portfolio contract. No user-supplied KQL, targets or resource types."""
import copy
import hashlib
import json
import uuid
from pathlib import Path

from scripts.validate_detection import require, validate_rule

ROOT = Path(__file__).resolve().parents[1]
VERSION = "azure-activity-portfolio-1.0"
# Mapping denotes a candidate abuse behavior, never an automatic attack verdict.
SPECS = {
    "AZ-DET-003": ("Custom Role Definition Changed", "Medium", ["PrivilegeEscalation"], ["T1098"],
                   ["Microsoft.Authorization/roleDefinitions/write"], "single"),
    "AZ-DET-004": ("Network Security Rule Changed", "Low", [], [],
                   ["Microsoft.Network/networkSecurityGroups/securityRules/write",
                    "Microsoft.Network/networkSecurityGroups/securityRules/delete"], "single"),
    "AZ-DET-005": ("Key Vault Access Policy Changed", "Medium", ["Persistence", "PrivilegeEscalation"], ["T1098"],
                   ["Microsoft.KeyVault/vaults/accessPolicies/write"], "single"),
    "AZ-DET-006": ("Virtual Machine Run Command", "Medium", ["Execution"], ["T1651"],
                   ["Microsoft.Compute/virtualMachines/runCommand/action"], "single"),
    "AZ-DET-007": ("Storage Account Keys Listed", "Low", ["CredentialAccess"], [],
                   ["Microsoft.Storage/storageAccounts/listKeys/action"], "single"),
    "AZ-DET-008": ("Resource Lock Removed", "Low", [], [],
                   ["Microsoft.Authorization/locks/delete"], "single"),
    "AZ-DET-009": ("Activity Log Alert Deleted", "Medium", ["DefenseEvasion"], ["T1562"],
                   ["Microsoft.Insights/activityLogAlerts/delete"], "single"),
    "AZ-DET-010": ("Policy Assignment Deleted", "Low", [], [],
                   ["Microsoft.Authorization/policyAssignments/delete"], "single"),
    "AZ-DET-011": ("Repeated Failed Privileged Operations", "Medium", [], [],
                   ["Microsoft.Authorization/roleAssignments/write", "Microsoft.Authorization/roleDefinitions/write"], "burst"),
    "AZ-DET-012": ("Role Grant Followed by Diagnostic Change", "High", ["Persistence", "PrivilegeEscalation", "DefenseEvasion"],
                   ["T1098", "T1562"], ["Microsoft.Authorization/roleAssignments/write",
                   "Microsoft.Insights/diagnosticSettings/write", "Microsoft.Insights/diagnosticSettings/delete"], "sequence"),
}
DESCRIPTIONS = {
    "AZ-DET-003": "Successful custom role definition write. Inspect permission deltas and existing assignments; a write does not prove new privileges.",
    "AZ-DET-004": "Successful NSG security rule write/delete. Inspect direction, priority and effective access; the event alone does not prove public exposure.",
    "AZ-DET-005": "Successful legacy Key Vault access policy write. Inspect principal and permission deltas; this does not observe secret reads or Azure RBAC assignments.",
    "AZ-DET-006": "Successful VM Run Command control-plane action. Investigate the request and guest evidence; this does not prove malicious guest execution.",
    "AZ-DET-007": "Successful storage account key-list action. Ordinary portal/automation also matches; no key material is queried or included.",
    "AZ-DET-008": "Successful resource lock deletion. Check authorization and subsequent writes/deletions; this does not prove destruction.",
    "AZ-DET-009": "Successful Activity Log alert deletion. Check ownership and replacement monitoring; deletion does not stop Activity Log collection.",
    "AZ-DET-010": "Successful Azure Policy assignment deletion. Inspect the removed policy and exemptions; the assignment may be unrelated to security.",
    "AZ-DET-011": "At least five distinct failed RBAC assignment/role definition writes by one caller in one resource group and fixed ten-minute bin. These are operational failures, not necessarily authorization denials or an attack.",
    "AZ-DET-012": "Successful role assignment followed strictly within fifteen minutes by a diagnostic setting write/delete by the same caller in the same resource group. Resource-group correlation does not prove equal RBAC/diagnostic target scope or causal privilege use.",
}
PROJECTION = ("TimeGenerated, OperationNameValue, ActivityStatusValue, Caller, SourceIPAddress, "
              "TargetResourceId, ResourceGroup, CorrelationId, EventDataId")
IP = '| extend SourceIPAddress = iff(CallerIpAddress !contains "/" and isnotempty(parse_ipv6(CallerIpAddress)), CallerIpAddress, "")'


def resource_uuid(key):
    require(key in SPECS, "Unapproved portfolio detection")
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "https://github.com/miguelcastu/SentinelOps-MXDR/" + key))


def query_for(key):
    _, _, _, _, operations, kind = SPECS[key]
    status = ["Failed", "Failure"] if kind == "burst" else ["Success", "Succeeded"]
    lines = ["AzureActivity", "| where TimeGenerated between (ago(1h) .. now())",
             "| where OperationNameValue in~ (" + ", ".join(json.dumps(x) for x in operations) + ")",
             "| where ActivityStatusValue in~ (" + ", ".join(json.dumps(x) for x in status) + ")",
             '| where isnotempty(EventDataId)',
             "| extend TargetResourceId = coalesce(ResourceId, _ResourceId)", IP,
             "| project " + PROJECTION,
             "| summarize arg_max(TimeGenerated, *) by EventDataId"]
    if kind == "single":
        return "\n".join(lines) + "\n"
    lines += ['| where isnotempty(Caller) and isnotempty(ResourceGroup)',
              '| extend CallerKey = tolower(Caller), ScopeKey = tolower(ResourceGroup)']
    if kind == "burst":
        lines += ["| summarize FailureCount=count(), FirstSeen=min(TimeGenerated), TimeGenerated=max(TimeGenerated), EventIds=make_set(EventDataId, 100), Operations=make_set(OperationNameValue, 10) by CallerKey, ScopeKey, WindowStart=bin(TimeGenerated, 10m)",
                  "| where FailureCount >= 5",
                  "| project TimeGenerated, FirstSeen, Caller=CallerKey, ResourceGroup=ScopeKey, FailureCount, WindowStart, EventIds, Operations"]
        return "\n".join(lines) + "\n"
    return ("let activity = materialize(\n" + "\n".join(lines) + "\n);\n"
            'let grants = activity\n| where OperationNameValue =~ "Microsoft.Authorization/roleAssignments/write"\n'
            '| project CallerKey, ScopeKey, RoleTime=TimeGenerated, RoleEventDataId=EventDataId, RoleResourceId=TargetResourceId;\n'
            'activity\n| where OperationNameValue in~ ("Microsoft.Insights/diagnosticSettings/write", "Microsoft.Insights/diagnosticSettings/delete")\n'
            '| join kind=inner grants on CallerKey, ScopeKey\n'
            '| where TimeGenerated > RoleTime and TimeGenerated <= RoleTime + 15m\n'
            '| extend RoleOrderKey = strcat(format_datetime(RoleTime, "yyyyMMddHHmmssfffffff"), "|", RoleEventDataId)\n'
            '| summarize arg_max(RoleOrderKey, *) by EventDataId\n'
            '| project ' + PROJECTION + ', RoleTime, RoleEventDataId, RoleResourceId\n')


def definition(key):
    title, severity, tactics, techniques, _, kind = SPECS[key]
    # Reuse the already accepted REST shape, never its query or target.
    body = json.loads((ROOT / "detections/azure/AZ-DET-002.json").read_text(encoding="utf-8"))
    props = body["properties"]
    props.update(displayName=key + " - " + title, severity=severity, tactics=tactics[:], techniques=techniques[:],
                 description=DESCRIPTIONS[key] + " Disabled lab definition; no incident creation or automation.", query=query_for(key))
    if kind == "burst":
        # Caller may be a GUID, UPN or application claim. Do not invent Account identifiers.
        props["entityMappings"] = []
        props["customDetails"] = {"Caller": "Caller", "FailureCount": "FailureCount", "ResourceGroup": "ResourceGroup"}
    if kind == "sequence":
        props["customDetails"]["RoleEventDataId"] = "RoleEventDataId"
    return copy.deepcopy(body)


def fingerprint():
    value = {"version": VERSION, "rules": {k: {"uuid": resource_uuid(k), "body": definition(k)} for k in SPECS}}
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate():
    # The shared REST skeleton must still satisfy its original strict contract.
    validate_rule(detection="AZ-DET-002")
    for key in SPECS:
        rule = json.loads((ROOT / f"detections/azure/{key}.json").read_text(encoding="utf-8"))
        query = (ROOT / f"detections/azure/{key}.kql").read_text(encoding="utf-8")
        require(rule == definition(key), f"{key}: definition differs from the reviewed fixed contract")
        require(query == query_for(key), f"{key}: KQL differs from the reviewed fixed contract")
    return fingerprint()
