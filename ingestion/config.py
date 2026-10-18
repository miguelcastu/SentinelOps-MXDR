"""Render proposed REST resource bodies offline; this module cannot deploy resources."""
import json
import re
import uuid
from pathlib import Path

from ingestion.events import COLUMNS, STREAM, TABLE

ROOT = Path(__file__).resolve().parents[1]
DCR_NAME = "dcr-sentinelops-synthetic-auth"
WORKSPACE_PATTERN = (r"/subscriptions/[0-9a-f-]{36}/resourceGroups/rg-sentinelops-mxdr/providers/"
                     r"Microsoft\.OperationalInsights/workspaces/law-sentinelops-mxdr-euw")


def configuration(workspace_id):
    if not isinstance(workspace_id, str) or not re.fullmatch(WORKSPACE_PATTERN, workspace_id):
        raise ValueError("Ingestion configuration requires the pinned existing lab workspace")
    subscription = workspace_id.split("/")[2]
    if str(uuid.UUID(subscription)) != subscription or not uuid.UUID(subscription).int:
        raise ValueError("A canonical non-placeholder subscription is required")
    table = json.loads((ROOT / "infrastructure/ingestion/table.json").read_text(encoding="utf-8"))
    dcr = json.loads((ROOT / "infrastructure/ingestion/dcr.template.json").read_text(encoding="utf-8"))
    expected = [{"name": name, "type": kind} for name, kind in COLUMNS.items()]
    if table["properties"]["schema"] != {"name": TABLE, "columns": expected}:
        raise ValueError("Custom table schema does not match the normalized event contract")
    props = dcr["properties"]
    if (set(dcr) != {"location", "kind", "properties"} or dcr["location"] != "westeurope" or
            dcr["kind"] != "Direct" or set(props) != {"streamDeclarations", "destinations", "dataFlows"} or
            props["destinations"] != {"logAnalytics": [{"name": "lab-workspace",
                "workspaceResourceId": "<PINNED_EXISTING_WORKSPACE_RESOURCE_ID>"}]} or
            set(table) != {"properties"} or set(table["properties"]) != {"plan", "schema"} or
            table["properties"]["plan"] != "Analytics"):
        raise ValueError("Unapproved resource configuration or extra destination")
    if props["streamDeclarations"] != {STREAM: {"columns": expected}}:
        raise ValueError("DCR input schema does not match the normalized event contract")
    if props["dataFlows"] != [{"streams": [STREAM], "destinations": ["lab-workspace"],
                                "transformKql": "source", "outputStream": "Custom-" + TABLE}]:
        raise ValueError("Unapproved transform or destination table")
    props["destinations"]["logAnalytics"][0]["workspaceResourceId"] = workspace_id
    return table, dcr
