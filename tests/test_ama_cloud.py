"""Cloud approval, ownership, missing-resource and exact-write boundaries."""
import copy
import contextlib
import io
import os
import unittest
import urllib.error
import tempfile
from pathlib import Path
from unittest.mock import patch

from ama.cloud import Client, MARKER, ROLES, contract, fingerprint, matches
from scripts import deploy_ama_pilot as deployment
from scripts.prepare_ama import ensure_exact_assignment
from scripts import bootstrap_ama_resources as bootstrap_resources

WORKSPACE = "/subscriptions/11111111-1111-4111-8111-111111111111/resourceGroups/rg-sentinelops-mxdr/providers/Microsoft.OperationalInsights/workspaces/law-sentinelops-mxdr-euw"


class CloudMemory:
    def __init__(self):
        self.spec = contract(WORKSPACE)
        self.values = {WORKSPACE: {"id": WORKSPACE, "location": "westeurope", "properties": {"sku": {"name": "pergb2018"}, "retentionInDays": 30, "workspaceCapping": {"dailyQuotaGb": 0.1}}},
                       self.spec["machine_id"]: {"id": self.spec["machine_id"], "location": "westeurope", "properties": {"status": "Connected", "osType": "linux"}, "identity": {"type": "SystemAssigned"}}}
        self.writes = []

    def request(self, method, path, body=None, missing_ok=False):
        target = path.split("?", 1)[0]
        if method == "PUT":
            self.writes.append((target, copy.deepcopy(body)))
            self.values[target] = copy.deepcopy(body) | {"id": target}
            self.values[target]["properties"]["provisioningState"] = "Succeeded"
        if target.endswith(("/extensions", "/dataCollectionRuleAssociations")):
            return {"value": [v for k, v in self.values.items() if k.rsplit("/", 1)[0] == target]}
        if target not in self.values:
            if missing_ok:
                return None
            raise ValueError("Unexpected resource request")
        return copy.deepcopy(self.values[target])


class TestAMACloud(unittest.TestCase):
    def test_personal_bootstrap_missing_or_wrong_extra_approval_never_authenticates(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            approval = root / ".local/ama/one-time-bootstrap-approved.json"
            approval.parent.mkdir(parents=True)
            with contextlib.redirect_stdout(io.StringIO()), patch.object(bootstrap_resources, "ROOT", root), patch.object(bootstrap_resources, "Client") as client, patch.object(bootstrap_resources, "az_json") as cli:
                bootstrap_resources.bootstrap(False)
                with self.assertRaises(FileNotFoundError):
                    bootstrap_resources.bootstrap(True)
                approval.write_text('{"allow_one_time_personal_bootstrap": false, "sha256": "wrong"}')
                with self.assertRaises(ValueError):
                    bootstrap_resources.bootstrap(True)
                client.assert_not_called()
                cli.assert_not_called()

    def test_exact_rbac_uses_arm_once_without_cli_scope_resolution(self):
        principal = "22222222-2222-4222-8222-222222222222"
        role = {"id": "/synthetic-role"}
        scope = contract(WORKSPACE)["dcr_id"]
        rows, writes = [], []
        class ArmMemory:
            def request(self, method, path, body=None):
                if method == "GET":
                    self_test.assertEqual(path, "/synthetic-principal-assignment-list")
                    return {"value": copy.deepcopy(rows)}
                self_test.assertTrue(path.startswith(scope + "/providers/Microsoft.Authorization/roleAssignments/"))
                writes.append(path)
                result = {"properties": body["properties"] | {"scope": scope}}
                rows.append(result)
                return result
        self_test = self
        arm = ArmMemory()
        with patch("scripts.prepare_ama.az_json") as cli:
            ensure_exact_assignment(arm, "/synthetic-principal-assignment-list", principal, role, scope)
            ensure_exact_assignment(arm, "/synthetic-principal-assignment-list", principal, role, scope)
            cli.assert_not_called()
        self.assertEqual(len(writes), 1)
        self.assertEqual(rows[0]["properties"]["principalId"], principal)

    def test_rbac_duplicate_or_different_principal_stops_without_put(self):
        principal = "22222222-2222-4222-8222-222222222222"
        scope = contract(WORKSPACE)["dcr_id"]
        row = {"properties": {"scope": scope, "roleDefinitionId": "/synthetic-role", "principalId": principal}}
        from unittest.mock import Mock
        for rows in ([row, row], [{"properties": row["properties"] | {"principalId": "other"}}]):
            arm = Mock()
            arm.request.return_value = {"value": rows}
            with self.assertRaises(ValueError):
                ensure_exact_assignment(arm, "/synthetic-list", principal, {"id": "/synthetic-role"}, scope)
            self.assertEqual(arm.request.call_count, 1)

    def test_missing_approval_stops_before_authentication_or_network(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(deployment, "Client") as client, patch.object(deployment, "context") as context:
            with self.assertRaises(ValueError):
                deployment.deploy()
            client.assert_not_called()
            context.assert_not_called()

    def test_success_writes_exactly_three_targets_and_is_idempotent(self):
        memory = CloudMemory()
        with contextlib.redirect_stdout(io.StringIO()), patch.dict(os.environ, {"SENTINEL_AMA_APPROVED_SHA256": fingerprint()}), patch.object(deployment, "context", return_value=WORKSPACE), patch.object(deployment, "Client", return_value=memory), patch.object(deployment, "complete_inventory", return_value=[]):
            deployment.deploy()
            deployment.deploy()
        self.assertEqual([target for target, _ in memory.writes], [memory.spec[k + "_id"] for k in ("dcr", "extension", "association")])
        self.assertTrue(all("delete" not in action.lower() and "*" not in action for _, actions in ROLES.values() for action in actions))
        self.assertTrue(all(action.endswith("/read") for action in ROLES["machine"][1]))

    def test_foreign_owner_extra_collection_or_association_stops_before_any_write(self):
        for mutation in ("foreign-owner", "extra-facility", "extra-association"):
            memory = CloudMemory()
            if mutation == "extra-association":
                memory.values[memory.spec["association_id"] + "-other"] = {"id": memory.spec["association_id"] + "-other"}
            else:
                dcr = copy.deepcopy(memory.spec["dcr"]) | {"id": memory.spec["dcr_id"]}
                if mutation == "foreign-owner":
                    dcr["tags"] = {"deployment-owner": "other"}
                else:
                    dcr["properties"]["dataSources"]["syslog"][0]["facilityNames"].append("auth")
                memory.values[memory.spec["dcr_id"]] = dcr
            with patch.dict(os.environ, {"SENTINEL_AMA_APPROVED_SHA256": fingerprint()}), patch.object(deployment, "context", return_value=WORKSPACE), patch.object(deployment, "Client", return_value=memory), patch.object(deployment, "complete_inventory", return_value=[]):
                with self.assertRaises(ValueError):
                    deployment.deploy()
            self.assertEqual(memory.writes, [])

    def test_http_permission_error_is_never_absence(self):
        client = object.__new__(Client)
        client.token = "synthetic-token"
        for status, code, absent in ((403, "AuthorizationFailed", False), (404, "UnknownError", False), (404, "ResourceNotFound", True)):
            failure = urllib.error.HTTPError("https://management.azure.com/synthetic", status, "synthetic", {}, io.BytesIO(('{"error":{"code":"' + code + '"}}').encode()))
            with patch("ama.cloud.urllib.request.build_opener") as opener:
                opener.return_value.open.side_effect = failure
                if absent:
                    self.assertIsNone(client.request("GET", "/synthetic", missing_ok=True))
                else:
                    with self.assertRaises(ValueError):
                        client.request("GET", "/synthetic", missing_ok=True)

    def test_extension_contract_rejects_command_settings_or_other_publisher(self):
        spec = contract(WORKSPACE)
        extension = copy.deepcopy(spec["extension"]) | {"id": spec["extension_id"]}
        self.assertTrue(matches(extension, spec["extension"], spec["extension_id"], "extension"))
        for change in ({"settings": {"commandToExecute": "unapproved"}}, {"publisher": "other"}, {"enableAutomaticUpgrade": True}):
            modified = copy.deepcopy(extension)
            modified["properties"].update(change)
            self.assertFalse(matches(modified, spec["extension"], spec["extension_id"], "extension"))
