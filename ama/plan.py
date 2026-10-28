"""Fixed AMA pilot contract. Rendering is offline and never provisions resources."""
import hashlib
import json
import re

MACHINE = "lab-sentinelops-linux-01"
DCR = "dcr-sentinelops-ama-linux"
EXTENSION = "AzureMonitorLinuxAgent"
ASSOCIATION = "sentinelops-ama-linux"
FACILITIES = ["local4"]
LEVELS = ["Warning", "Error", "Critical", "Alert", "Emergency"]


def resources(workspace_id):
    if not isinstance(workspace_id, str) or not re.fullmatch(r"/subscriptions/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/resourceGroups/rg-sentinelops-mxdr/providers/Microsoft.OperationalInsights/workspaces/law-sentinelops-mxdr-euw", workspace_id):
        raise ValueError("Only the pinned existing workspace can be rendered")
    group = workspace_id.split("/providers/", 1)[0]
    machine = group + "/providers/Microsoft.HybridCompute/machines/" + MACHINE
    dcr_id = group + "/providers/Microsoft.Insights/dataCollectionRules/" + DCR
    dcr = {"location": "westeurope", "kind": "Linux", "properties": {
        "dataSources": {"syslog": [{"name": "lab-local4-warning", "streams": ["Microsoft-Syslog"],
                                    "facilityNames": FACILITIES[:], "logLevels": LEVELS[:]}]},
        "destinations": {"logAnalytics": [{"name": "existing-workspace", "workspaceResourceId": workspace_id}]},
        "dataFlows": [{"streams": ["Microsoft-Syslog"], "destinations": ["existing-workspace"]}]}}
    extension = {"location": "westeurope", "properties": {"publisher": "Microsoft.Azure.Monitor",
                 "type": EXTENSION, "typeHandlerVersion": "1.0", "autoUpgradeMinorVersion": True,
                 "enableAutomaticUpgrade": True, "settings": {}}}
    association = {"properties": {"dataCollectionRuleId": dcr_id,
                   "description": "Single owned local machine; local4 warning pilot only"}}
    return {"machine_id": machine, "dcr_id": dcr_id,
            "extension_id": machine + "/extensions/" + EXTENSION,
            "association_id": machine + "/providers/Microsoft.Insights/dataCollectionRuleAssociations/" + ASSOCIATION,
            "dcr": dcr, "extension": extension, "association": association}


def validate_dcr(body, workspace_id):
    if body != resources(workspace_id)["dcr"]:
        raise ValueError("DCR changed: broad collection, destinations or streams are prohibited")


def public_plan():
    return {"source_id": "ama-linux-syslog", "machine": MACHINE, "os": "Ubuntu 24.04 LTS amd64",
            "hosting": "local VirtualBox; no Azure compute", "ram_mib": 1536, "vcpus": 1,
            "network": "NAT; SSH 127.0.0.1:22221 only", "paravirtualization": "kvm; single CPU; APIC enabled",
            "workspace": "law-sentinelops-mxdr-euw",
            "region": "westeurope", "table": "Syslog", "facilities": FACILITIES[:], "levels": LEVELS[:],
            "test_events": 10, "test_max_bytes": 4096, "azure_changes_executed": False,
            "limitations": ["Cloud resources and live ingestion require the separate fixed-scope rollout approval.",
                            "Syslog is potentially billable; no recurring paid feature is authorized.",
                            "local4 pilot does not collect SSH authentication, Windows events or Sysmon.",
                            "Machine registration, AMA provisioning and queried ingestion are separate evidence stages."]}


def fingerprint():
    return hashlib.sha256(json.dumps(public_plan(), sort_keys=True).encode()).hexdigest()
