"""Bounded, labeled pilot payloads. This module never sends a message."""
import re

EVENTS = 10
MAX_BYTES = 4096


def messages(run_id):
    if not isinstance(run_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{7,47}", run_id):
        raise ValueError("Pilot run ID must contain 8-48 lowercase ASCII letters, digits or hyphens")
    result = [f"SENTINELOPS_AMA_PILOT run={run_id} seq={index:02d}/{EVENTS} synthetic=true"
              for index in range(1, EVENTS + 1)]
    if sum(len((message + "\n").encode("utf-8")) for message in result) > MAX_BYTES:
        raise ValueError("Pilot payload exceeds its byte allowance")
    return result
