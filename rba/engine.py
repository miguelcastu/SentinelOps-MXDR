"""Deterministic rolling entity risk, bounded scoring and an ordered multi-stage rule."""
import hashlib
import json
import uuid
from collections import defaultdict
from datetime import timedelta

from rba.model import HEALTH_STATES, SOURCES, baseline_match, baselines, instant, load_policy, require, signal


def deduplicate(events, policy):
    by_id, by_original, result = {}, {}, []
    for raw in events:
        event = signal(raw, policy)
        encoded = json.dumps(event, sort_keys=True)
        original = json.dumps({k:v for k,v in event.items() if k != "event_id"}, sort_keys=True)
        original_key = (event["source"], event["source_event_id"])
        require(event["event_id"] not in by_id or by_id[event["event_id"]] == encoded)
        require(original_key not in by_original or by_original[original_key] == original)
        duplicate = event["event_id"] in by_id or original_key in by_original
        by_id[event["event_id"]] = encoded
        by_original[original_key] = original
        if not duplicate:
            canonical_id = "synthetic-" + uuid.uuid5(uuid.NAMESPACE_URL, event["source"] + "/" + event["source_event_id"]).hex
            result.append(dict(event, event_id=canonical_id))
    return sorted(result, key=lambda e:(instant(e["time"]), e["event_id"]))


def ordered_chain(events, entries, policy):
    require(len({event["actor"] for event in events}) <= 1)
    failures, authenticated, roles, diagnostics = defaultdict(list), {}, {}, {}
    best = None
    span = timedelta(minutes=policy["sequence_span_minutes"])
    for event in events:
        time = instant(event["time"])
        kind = event["kind"]
        key = (event["host"], event["source_ip"])
        if kind == "authentication_failure":
            failures[key].append(event)
        elif kind == "authentication_success":
            recent = [e for e in failures[key] if time - timedelta(minutes=10) <= instant(e["time"]) < time]
            if len(recent) >= 3:
                authenticated[key] = {"events": recent[-3:] + [event], "start": instant(recent[-3]["time"]),
                                      "time": time, "host": event["host"], "ip": event["source_ip"]}
        elif kind == "rbac_assignment" and baseline_match(event, entries) is None:
            for context_key, context in authenticated.items():
                if context["time"] < time and time - context["start"] <= span:
                    roles[(event["resource"], *context_key)] = dict(context, events=context["events"] + [event], time=time)
        elif kind == "diagnostic_change" and baseline_match(event, entries) is None:
            for context_key, context in roles.items():
                if (context_key[0] == event["resource"] and context["time"] < time and
                        time - context["time"] <= timedelta(minutes=15) and time - context["start"] <= span):
                    diagnostics[context_key] = dict(context, events=context["events"] + [event], time=time)
        elif kind == "endpoint_execution":
            candidates = [dict(c, events=c["events"] + [event], time=time) for c in diagnostics.values()
                          if c["host"] == event["host"] and c["time"] < time and
                          time - c["time"] <= timedelta(minutes=15) and time - c["start"] <= span]
            if candidates:
                best = max(candidates, key=lambda c:(c["time"], c["start"], tuple(e["event_id"] for e in c["events"])))
    return best


def score_at(events, at, policy, entries):
    active = [e for e in events if at - timedelta(minutes=policy["window_minutes"]) <= instant(e["time"]) <= at]
    rows, by_kind = [], defaultdict(float)
    for event in active:
        rule = policy["signals"][event["kind"]]
        exception = baseline_match(event, entries)
        factor = exception["factor"] if exception else 1
        age = (at - instant(event["time"])).total_seconds() / 60
        decay = 2 ** (-age / policy["half_life_minutes"])
        points = rule["points"] * rule["confidence"] * factor * decay
        rows.append({"event_id":event["event_id"], "source_event_id":event["source_event_id"], "time":event["time"],
                     "kind":event["kind"], "source":event["source"], "base_points":rule["points"],
                     "signal_confidence":rule["confidence"], "severity":rule["severity"],
                     "baseline_change":exception["change_id"] if exception else None, "baseline_factor":factor,
                     "decay_factor":decay, "before_caps":points, "points":points})
        by_kind[event["kind"]] += points
    for row in rows:
        total = by_kind[row["kind"]]
        row["points"] *= min(1, policy["signals"][row["kind"]]["cap"] / total) if total else 0
    chain = ordered_chain(active, entries, policy)
    bonus = policy["sequence_bonus"] * 2 ** (-(at - chain["time"]).total_seconds() / 60 / policy["half_life_minutes"]) if chain else 0
    uncapped = sum(r["points"] for r in rows) + bonus
    scale = min(1, 100 / uncapped) if uncapped else 1
    for row in rows:
        row["points"] *= scale
    bonus *= scale
    score = min(100, uncapped)
    families = sorted({policy["signals"][e["kind"]]["family"] for e in active})
    sources = sorted({e["source"] for e in active})
    eligible = bool(score >= policy["finding_threshold"] and chain and len(families) >= 3 and len(sources) >= 2)
    return {"time":at.isoformat().replace("+00:00", "Z"), "score":round(score, 4),
            "eligible":eligible, "priority":"High" if score >= 60 else "Medium" if score >= 40 else "Low" if score >= 20 else "Informational",
            "families":families, "sources":sources, "sequence_bonus":round(bonus, 4),
            "chain_event_ids":[e["event_id"] for e in chain["events"]] if chain else [],
            "contributions":[{k:round(v, 6) if isinstance(v, float) else v for k,v in r.items()} for r in rows]}


def health_context(value, as_of):
    require(isinstance(value, dict) and set(value) == {"evidence", "observed_at", "states"})
    require(value["evidence"] in ("synthetic", "imported-health"))
    require(isinstance(value["states"], dict) and set(value["states"]) == SOURCES)
    require(all(state in HEALTH_STATES for state in value["states"].values()))
    fresh = 0 <= (as_of - instant(value["observed_at"])).total_seconds() <= 900
    return {"evidence":value["evidence"], "observed_at":value["observed_at"], "fresh":fresh,
            "states":dict(value["states"]) if fresh else {source:"Unknown" for source in sorted(SOURCES)}}


def correlate(dataset, as_of=None):
    require(isinstance(dataset, dict) and set(dataset) == {"schema_version", "evidence", "customer", "as_of", "events", "health"})
    require(dataset["schema_version"] == "1.0" and dataset["evidence"] == "synthetic" and dataset["customer"] == "Atlas Financial")
    policy = load_policy()
    at = instant(as_of or dataset["as_of"])
    require(isinstance(dataset["events"], list) and len(dataset["events"]) <= policy["max_events"])
    events = deduplicate(dataset["events"], policy)
    require(all(instant(e["time"]) <= at for e in events))
    retained = [e for e in events if instant(e["time"]) >= at - timedelta(minutes=policy["lookback_minutes"])]
    grouped = defaultdict(list)
    for event in retained:
        grouped[event["actor"]].append(event)
    require(len(grouped) <= policy["max_actors"])
    entries, health = baselines(policy), health_context(dataset["health"], at)
    configuration_hash = hashlib.sha256(json.dumps({"catalog":policy, "baselines":entries},
        sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    entities, findings = [], []
    for actor in sorted(grouped):
        actor_events = grouped[actor]
        times = sorted({instant(e["time"]) for e in actor_events} | {at})
        timeline, peak, first = [], None, None
        for time in times:
            point = score_at(actor_events, time, policy, entries)
            timeline.append({k:v for k,v in point.items() if k not in ("contributions", "chain_event_ids")})
            if peak is None or point["score"] > peak["score"]:
                peak = point
            if point["eligible"] and first is None:
                first = point
        current = score_at(actor_events, at, policy, entries)
        related = sorted({(key, e[key]) for e in actor_events for key in ("host", "source_ip", "resource") if e[key] is not None})
        entities.append({"entity_type":"Account", "entity_id":actor, "current":current, "peak":peak,
                         "related_entities":[{"type":k, "value":v} for k,v in related], "timeline":timeline})
        if first:
            chain_ids = first["chain_event_ids"]
            fingerprint = configuration_hash + actor + "/".join(chain_ids)
            finding_id = "synthetic-finding-" + uuid.uuid5(uuid.NAMESPACE_URL, fingerprint).hex
            used = {e["source"] for e in actor_events if e["event_id"] in chain_ids}
            limited = sorted(s for s in used if health["states"][s] not in ("Healthy", "Delayed"))
            findings.append({"finding_id":finding_id, "evidence":"synthetic", "entity_id":actor,
                "rule":"AF-RBA-001", "first_detected":first["time"], "first_score":first["score"],
                "peak_score":peak["score"], "current_score":current["score"], "priority":first["priority"],
                "confidence":"Low" if limited else "Medium", "confidence_is_calibrated":False,
                "health_limitations":limited, "chain_event_ids":chain_ids,
                "evidence_chain":[next(e for e in actor_events if e["event_id"] == event_id) for event_id in chain_ids],
                "techniques":sorted({t for e in actor_events if e["event_id"] in chain_ids for t in policy["signals"][e["kind"]]["techniques"]}),
                "investigation_steps":["Verify identity mapping and original event IDs.", "Check the exact role, scope and change approval.",
                    "Confirm diagnostic changes reduced visibility before alleging tampering.", "Review authentication context and endpoint process evidence.",
                    "Treat Unknown collection health as an evidence gap; preserve event order and timestamps."],
                "sentinel_incident_created":False})
    digest = hashlib.sha256(json.dumps(events, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {"schema_version":"1.0", "evidence":"synthetic", "customer":"Atlas Financial", "as_of":at.isoformat().replace("+00:00", "Z"),
            "policy_version":policy["policy_version"], "configuration_sha256":configuration_hash, "dataset_sha256":digest,
            "counts":{"input":len(dataset["events"]), "unique":len(events), "duplicates":len(dataset["events"]) - len(events),
                      "outside_lookback":len(events) - len(retained), "entities":len(entities), "findings":len(findings)},
            "policy":{k:policy[k] for k in ("window_minutes", "lookback_minutes", "half_life_minutes", "finding_threshold")},
            "health_context":health, "entities":entities, "findings":findings,
            "limits":{"network_calls":0, "azure_changes":0, "sentinel_incidents_created":0, "live_telemetry_validated":False}}
