"""Manual read-only comparison of the existing rule with its approved source."""
import os

from scripts.azure_guard import az_json, context, rule_url
from scripts.validate_detection import DISPLAY_NAME, require, validate_rule


def changed_properties(current, expected):
    properties = current.get("properties", {})
    return [key for key, value in expected["properties"].items() if properties.get(key) != value]


def check():
    desired = validate_rule()
    workspace_id = context("check-drift.yml")
    url = rule_url(workspace_id, os.environ.get("SENTINEL_RULE_ID", ""))
    current = az_json("rest", "--method", "get", "--url", url)
    expected_id = url.removeprefix("https://management.azure.com").split("?", 1)[0]
    require(current.get("id", "").lower() == expected_id.lower(), "Drift target ID mismatch")
    require(current.get("kind") == "Scheduled" and current.get("properties", {}).get("displayName") == DISPLAY_NAME,
            "Drift target kind/name mismatch")
    changed = changed_properties(current, desired)
    require(not changed, "Configuration drift detected in: " + ", ".join(changed))
    print("PASS: Azure GET matches approved AZ-DET-001 source, enabled=false; no changes performed")


if __name__ == "__main__":
    try:
        check()
    except (ValueError, OSError) as exc:
        raise SystemExit(str(exc)) from None
