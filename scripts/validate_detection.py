"""Validate the narrow rule schema and the supported KQL contract offline."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULE = ROOT / "detections/azure/AZ-DET-001.json"
KQL = ROOT / "detections/azure/AZ-DET-001.kql"
SCHEMA = ROOT / "schemas/scheduled-rule.schema.json"
DISPLAY_NAME = "AZ-DET-001 - Azure Diagnostic Settings Modified"
OPERATIONS = {
    "microsoft.insights/diagnosticsettings/write",
    "microsoft.insights/diagnosticsettings/delete",
}
STATUSES = {"success", "succeeded"}
PROJECT = ("TimeGenerated, OperationNameValue, ActivityStatusValue, Caller, "
           "SourceIPAddress, TargetResourceId, ResourceGroup, CorrelationId, EventDataId")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_schema(value, schema, path="$ "):
    """Evaluate only the JSON Schema keywords used by this repository's schema.

    This is deliberately not a general JSON Schema implementation. Unknown schema
    keywords fail closed. A standards validator can independently check the schema.
    """
    supported = {"$schema", "title", "type", "const", "required", "properties",
                 "additionalProperties", "minLength", "maxLength"}
    require(not (set(schema) - supported), f"{path}: unsupported schema keyword")
    if "const" in schema:
        require(type(value) is type(schema["const"]) and
                json.dumps(value, sort_keys=True) == json.dumps(schema["const"], sort_keys=True),
                f"{path}: value is not approved")
    if "type" in schema:
        types = {"object": dict, "string": str}
        require(schema["type"] in types, f"{path}: unsupported schema type")
        require(type(value) is types[schema["type"]], f"{path}: wrong type")
    if isinstance(value, dict):
        require(set(schema.get("required", [])) <= set(value), f"{path}: missing fields")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            require(set(value) <= set(properties), f"{path}: unauthorized fields")
        for key in value.keys() & properties.keys():
            validate_schema(value[key], properties[key], f"{path}.{key}")
    if isinstance(value, str):
        require(len(value) >= schema.get("minLength", 0), f"{path}: too short")
        require(len(value) <= schema.get("maxLength", len(value)), f"{path}: too long")


def parse_predicates(query):
    """Parse this rule's three filters; reject arbitrary KQL and extra stages."""
    lines = [line.strip() for line in query.strip().splitlines()]
    require(len(lines) == 7 and lines[0] == "AzureActivity", "KQL must have the approved seven stages")
    match = re.fullmatch(r"\| where TimeGenerated between \(ago\((\d+)h\) \.\. now\(\)\)", lines[1])
    require(match is not None and match[1] == "1", "KQL must use the bounded one-hour window")
    predicates = []
    for line, column, expected in zip(lines[2:4], ("OperationNameValue", "ActivityStatusValue"), (OPERATIONS, STATUSES)):
        match = re.fullmatch(r"\| where " + column + r" in~ \((.*)\)", line)
        require(match is not None, f"Invalid {column} filter")
        try:
            values = json.loads("[" + match[1] + "]")
        except json.JSONDecodeError as exc:
            raise ValueError("Invalid KQL literal list") from exc
        require(all(isinstance(v, str) for v in values), "KQL literals must be strings")
        require(len(values) == len(expected) and {v.casefold() for v in values} == expected,
                f"Unapproved {column} values")
        predicates.append((column, {v.casefold() for v in values}))
    require(lines[4] == "| extend TargetResourceId = coalesce(ResourceId, _ResourceId)", "Invalid resource projection")
    require(lines[5] == '| extend SourceIPAddress = iff(CallerIpAddress !contains "/" and isnotempty(parse_ipv6(CallerIpAddress)), CallerIpAddress, "")', "Invalid IP projection")
    require(lines[6] == "| project " + PROJECT, "Invalid output columns")
    return 3600, predicates


def validate_rule(rule=None, query=None):
    rule = json.loads(RULE.read_text(encoding="utf-8")) if rule is None else rule
    query = KQL.read_text(encoding="utf-8") if query is None else query
    validate_schema(rule, json.loads(SCHEMA.read_text(encoding="utf-8")))
    require(rule["properties"]["query"] == query, "REST query must exactly match the KQL source")
    parse_predicates(query)
    return rule


if __name__ == "__main__":
    validate_rule()
    print("PASS: restricted REST schema, disabled rule, approved KQL and synchronized source")
