"""Update the single existing disabled rule, then verify persisted properties."""
import json
import os
import tempfile
from pathlib import Path

from scripts.azure_guard import az_json, context, rule_url
from scripts.validate_detection import DISPLAY_NAME, require, validate_rule


def verify_existing(current, expected_id):
    require(current.get("id", "").lower() == expected_id.lower(), "Cloud resource ID mismatch")
    require(current.get("type", "").lower() == "microsoft.securityinsights/alertrules", "Unauthorized resource type")
    require(current.get("kind") == "Scheduled", "Existing rule must be Scheduled")
    properties = current.get("properties", {})
    require(properties.get("displayName") == DISPLAY_NAME, "Existing rule name mismatch")
    require(properties.get("enabled") is False, "Existing rule must already be disabled; stop for operator review")
    require(bool(current.get("etag")), "An existing resource etag is required")


def deploy():
    rule = validate_rule()
    require(os.environ.get("SENTINEL_DEPLOYMENT_APPROVED") == "true", "Manual prerequisite review has not been recorded")
    require(os.environ.get("SENTINEL_EXCLUSIVE_RULE_OWNER") == "true", "Confirm Sentinel Repositories does not also manage this rule")
    workspace_id = context("deploy-sentinel.yml")
    url = rule_url(workspace_id, os.environ.get("SENTINEL_RULE_ID", ""))
    expected_id = url.removeprefix("https://management.azure.com").split("?", 1)[0]
    workspace = az_json("rest", "--method", "get", "--url", f"https://management.azure.com{workspace_id}?api-version=2025-02-01")
    require(workspace.get("id", "").lower() == workspace_id.lower(), "Workspace ID mismatch")
    require(workspace.get("location", "").lower() == "westeurope", "Workspace location mismatch")
    current = az_json("rest", "--method", "get", "--url", url)
    verify_existing(current, expected_id)
    # The RP's documented etag field provides optimistic concurrency. Never send
    # an unconditional upsert or silently retry a conflict with a fresh etag.
    payload = dict(rule, etag=current["etag"])
    with tempfile.TemporaryDirectory(prefix="sentinelops-") as directory:
        body = Path(directory) / "disabled-rule.json"
        body.write_text(json.dumps(payload), encoding="utf-8")
        response = az_json("rest", "--method", "put", "--url", url,
                           "--headers", f"If-Match={current['etag']}",
                           "--body", "@" + str(body))
    verify_existing(response, expected_id)
    persisted = az_json("rest", "--method", "get", "--url", url)
    verify_existing(persisted, expected_id)
    for key, value in rule["properties"].items():
        require(persisted["properties"].get(key) == value, f"Persisted property mismatch: {key}")
    print("PASS: Azure REST confirms the existing AZ-DET-001 rule matches source and remains disabled")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as stream:
            stream.write("AZ-DET-001 verified through Azure REST: existing resource updated, enabled=false, PT15M/PT1H. No identifiers or telemetry published.\n")


if __name__ == "__main__":
    try:
        deploy()
    except (ValueError, OSError, TimeoutError) as exc:
        raise SystemExit(f"Deployment stopped: {exc}") from None
