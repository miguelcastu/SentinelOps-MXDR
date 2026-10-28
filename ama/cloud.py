"""Fixed, explicitly authorized one-machine cloud contract; no network at import."""
import hashlib
import json
import re
import urllib.error
import urllib.request

from ama.plan import resources
from scripts.azure_guard import az_json
from scripts.prepare_portfolio import NoRedirect

MONITOR_API = "2024-03-11"
ARC_API = "2025-01-13"
MARKER = {"sentinelops-source": "ama-linux-syslog", "deployment-owner": "github-oidc"}
ROLES = {
    "machine": ("SentinelOps AMA Machine Metadata Reader", ["Microsoft.HybridCompute/machines/read", "Microsoft.HybridCompute/machines/extensions/read", "Microsoft.Insights/dataCollectionRuleAssociations/read"]),
    "dcr": ("SentinelOps AMA Fixed DCR Writer", ["Microsoft.Insights/dataCollectionRules/read", "Microsoft.Insights/dataCollectionRules/write"]),
    "extension": ("SentinelOps AMA Fixed Extension Writer", ["Microsoft.HybridCompute/machines/extensions/read", "Microsoft.HybridCompute/machines/extensions/write"]),
    "association": ("SentinelOps AMA Fixed Association Writer", ["Microsoft.Insights/dataCollectionRuleAssociations/read", "Microsoft.Insights/dataCollectionRuleAssociations/write"]),
}


def contract(workspace):
    value = resources(workspace)
    value["dcr"]["tags"] = dict(MARKER)
    value["dcr"]["properties"]["dataFlows"][0].update(transformKql="source", outputStream="Microsoft-Syslog")
    value["extension"]["tags"] = dict(MARKER)
    # No background extension upgrades or additional provider registration.
    value["extension"]["properties"]["enableAutomaticUpgrade"] = False
    return value


def fingerprint():
    placeholder = "/subscriptions/00000000-0000-4000-8000-000000000000/resourceGroups/rg-sentinelops-mxdr/providers/Microsoft.OperationalInsights/workspaces/law-sentinelops-mxdr-euw"
    value = {"resources": contract(placeholder), "roles": ROLES, "apis": [MONITOR_API, ARC_API],
             "pilot_events": 10, "pilot_bytes": 4096, "activation": False, "query": "manual aggregate only"}
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


class Client:
    """In-memory credentials, no redirects, bounded bodies, sanitized errors."""
    def __init__(self):
        self.token = az_json("account", "get-access-token", "--resource", "https://management.azure.com/")["accessToken"]

    def request(self, method, path, body=None, missing_ok=False):
        request = urllib.request.Request("https://management.azure.com" + path, method=method,
                    data=None if body is None else json.dumps(body).encode(),
                    headers={"Authorization": "Bearer " + self.token, "Content-Type": "application/json",
                             **({"If-None-Match": "*"} if method == "PUT" else {})})
        try:
            with urllib.request.build_opener(NoRedirect()).open(request, timeout=60) as response:
                raw = response.read(2_097_152)
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as exc:
            code = "AzureHTTPError"
            try:
                candidate = json.loads(exc.read(65536)).get("error", {}).get("code", "")
                if re.fullmatch(r"[A-Za-z][A-Za-z0-9]{0,80}", candidate):
                    code = candidate
            except (ValueError, AttributeError):
                pass
            if missing_ok and exc.code == 404 and code in {"ResourceNotFound", "NotFound"}:
                return None
            raise ValueError(f"Azure {method} failed (HTTP {exc.code}, {code}); no permission or subscription fallback") from None


def matches(current, desired, resource_id, kind):
    if not isinstance(current, dict) or current.get("id", "").lower() != resource_id.lower():
        return False
    if kind in ("dcr", "extension"):
        if current.get("location") != "westeurope" or current.get("tags") != MARKER:
            return False
    props = current.get("properties", {})
    if kind == "dcr":
        if current.get("kind") != "Linux":
            return False
        if any(props.get(key) for key in ("dataCollectionEndpointId", "streamDeclarations", "directDataSources", "references", "agentSettings")):
            return False
        # Reject extras inside collection/destination/flow structures as well.
        return all(props.get(key) == value for key, value in desired["properties"].items())
    if kind == "extension":
        allowed = {"publisher", "type", "typeHandlerVersion", "autoUpgradeMinorVersion", "enableAutomaticUpgrade", "settings", "provisioningState", "instanceView"}
        if set(props) - allowed or props.get("settings", {}) != {}:
            return False
        expected = desired["properties"]
        return (all(props.get(k) == v for k, v in expected.items() if k != "typeHandlerVersion") and
                str(props.get("typeHandlerVersion", "")).startswith("1."))
    if kind == "association":
        return props.get("dataCollectionRuleId", "").lower() == desired["properties"]["dataCollectionRuleId"].lower() and props.get("description") == desired["properties"]["description"] and not props.get("dataCollectionEndpointId")
    return False
