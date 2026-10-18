"""Adapt labeled synthetic AzureActivity and the existing authentication source contract."""
import json
import uuid

from ingestion.events import normalize
from rba.model import ROOT, load_policy, require, signal

OPERATIONS = {
    "microsoft.authorization/roleassignments/write": "rbac_assignment",
    "microsoft.insights/diagnosticsettings/write": "diagnostic_change",
    "microsoft.insights/diagnosticsettings/delete": "diagnostic_change",
    "microsoft.authorization/policyassignments/write": "policy_change",
}


def make_signal(source, original_id, time, kind, actor, host=None, source_ip=None, resource=None):
    event_id = "synthetic-" + uuid.uuid5(uuid.NAMESPACE_URL, source + "/" + original_id).hex
    return signal(dict(synthetic=True, event_id=event_id, source_event_id=original_id, time=time,
                       source=source, kind=kind, actor=actor, host=host, source_ip=source_ip, resource=resource), load_policy())


def authentication(raw):
    event = normalize(raw)
    return make_signal("synthetic-authentication", event["EventOriginalUid"], event["TimeGenerated"],
        "authentication_success" if event["EventResult"] == "Success" else "authentication_failure",
        event["TargetUsername"], event["DvcHostname"], event["SrcIpAddr"])


def azure_activity(raw):
    require(isinstance(raw, dict) and set(raw) == {"Synthetic", "EventDataId", "TimeGenerated", "OperationNameValue",
                                                 "ActivityStatusValue", "Caller", "CallerIpAddress", "ResourceId"})
    require(raw["Synthetic"] is True)
    aliases = json.loads((ROOT / "rba/entity-map.json").read_text(encoding="utf-8"))
    require(raw["Caller"] in aliases)
    require(isinstance(raw["OperationNameValue"], str) and isinstance(raw["ActivityStatusValue"], str))
    kind = OPERATIONS.get(raw["OperationNameValue"].casefold())
    if kind is None or raw["ActivityStatusValue"].casefold() not in ("success", "succeeded", "failure", "failed"):
        return None
    if raw["ActivityStatusValue"].casefold() in ("failed", "failure"):
        kind = "administrative_failure"
    return make_signal("azure-activity", raw["EventDataId"], raw["TimeGenerated"], kind, aliases[raw["Caller"]],
                       source_ip=raw["CallerIpAddress"] or None, resource=raw["ResourceId"])
