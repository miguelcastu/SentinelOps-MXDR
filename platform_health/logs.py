"""Strict offline adapter for a future authorized aggregate query; never sends queries."""
from platform_health.engine import blank_observation, require

COLUMNS = ("TotalEvents", "ValidEvents", "DistinctEvents", "SchemaErrors", "MappingErrors",
           "NegativeLatencyEvents", "LastSeen", "LatencyP95Seconds", "BillableBytes")
FIELDS = ("total_events", "valid_events", "distinct_events", "schema_errors", "mapping_errors",
          "negative_latency_events", "last_seen", "latency_p95_seconds", "billable_bytes")


def observation(response, source_id, observed_at, window_start, window_end):
    require(isinstance(response, dict) and not response.get("error"))
    tables = response.get("tables", [])
    require(len(tables) == 1 and [c.get("name") for c in tables[0].get("columns", [])] == list(COLUMNS))
    rows = tables[0].get("rows", [])
    require(len(rows) == 1 and len(rows[0]) == len(FIELDS))
    result = blank_observation(source_id, observed_at, window_start)
    result.update(zip(FIELDS, rows[0]))
    result.update(query_status="success", window_end=window_end)
    # The engine validates types, count consistency and time boundaries before reporting.
    return result
