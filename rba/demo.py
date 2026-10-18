"""Fictional Atlas Financial compromise and maintenance controls; nothing is executed."""
import copy
import uuid

from ingestion.events import generate
from rba.adapters import authentication, azure_activity, make_signal

AS_OF = "2026-10-18T12:20:00Z"


def original(label):
    return "synthetic-" + uuid.uuid5(uuid.NAMESPACE_URL, "atlas-rba-demo/" + label).hex


def auth(minute, actor=0, success=False):
    time = f"2026-10-18T12:{minute:02}:00Z"
    raw = generate(1, time, f"risk-user-{actor:02}")[0]
    raw.update(event_code=4624 if success else 4625, username=f"synthetic-user-{actor:02}",
               hostname=f"lab-auth-{actor:02}", source_ip="192.0.2.10")
    return authentication(raw)


def admin(minute, kind, actor=0, success=True, resource=None):
    operation = {"rbac_assignment":"Microsoft.Authorization/roleAssignments/write",
                 "diagnostic_change":"Microsoft.Insights/diagnosticSettings/delete",
                 "policy_change":"Microsoft.Authorization/policyAssignments/write"}[kind]
    time = f"2026-10-18T12:{minute:02}:00Z"
    scope = resource or f"lab-resource-workspace-{actor + 1:02}"
    return azure_activity({"Synthetic":True, "EventDataId":original(f"{time}/{kind}/{actor}/{success}/{scope}"),
        "TimeGenerated":time, "OperationNameValue":operation, "ActivityStatusValue":"Success" if success else "Failed",
        "Caller":f"synthetic-principal-{actor:02}", "CallerIpAddress":"192.0.2.10",
        "ResourceId":scope})


def attack(actor=0):
    return [auth(0, actor), auth(1, actor), auth(2, actor), auth(3, actor, True),
            admin(6, "rbac_assignment", actor), admin(10, "diagnostic_change", actor),
            make_signal("synthetic-endpoint", original(f"endpoint-{actor}"), "2026-10-18T12:13:00Z",
                        "endpoint_execution", f"synthetic-user-{actor:02}", host=f"lab-auth-{actor:02}")]


def dataset(events=None):
    if events is None:
        events = attack() + attack(1) + [admin(4, "rbac_assignment", 2, False), admin(9, "policy_change", 2)]
        events += [copy.deepcopy(events[4]), dict(events[4], event_id=original("retry-envelope"))]
    return {"schema_version":"1.0", "evidence":"synthetic", "customer":"Atlas Financial", "as_of":AS_OF,
            "events":events, "health":{"evidence":"synthetic", "observed_at":AS_OF,
                "states":{"azure-activity":"Healthy", "synthetic-authentication":"Healthy", "synthetic-endpoint":"Unknown"}}}


def scenarios():
    cases = []

    def append(name, events, expected):
        cases.append({"scenario":name, "dataset":dataset(events), "expected_findings":expected})

    append("multi-stage-compromise", attack(), 1)
    append("approved-maintenance-lookalike", attack(1), 0)
    append("single-role-grant", [attack()[4]], 0)
    append("authentication-failures-only", [auth(i) for i in range(20)], 0)
    reversed_order = attack()
    reversed_order[4]["time"], reversed_order[5]["time"] = reversed_order[5]["time"], reversed_order[4]["time"]
    append("wrong-stage-order", reversed_order, 0)
    scope = attack()
    scope[5]["resource"] = "lab-resource-unrelated"
    append("unrelated-resource-scope", scope, 0)
    host = attack()
    host[-1]["host"] = "lab-auth-09"
    append("unrelated-endpoint-host", host, 0)
    split = attack()
    for event in split[4:]:
        event["actor"] = "synthetic-user-02"
    append("shared-ip-different-actors", split, 0)
    append("duplicate-replay", attack() + copy.deepcopy(attack()), 1)
    return cases
