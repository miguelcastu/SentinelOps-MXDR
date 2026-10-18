# Log source onboarding template

Use this record before configuring a source. The live inventory is [sources.json](../../ingestion/sources.json).

| Required field | Record before approval |
|---|---|
| Customer, owner, escalation contact | Fictional customer vs real operator; no personal details in public evidence |
| Source and event types | Vendor, transport, expected success/failure events and coverage gaps |
| Destination | Existing subscription, workspace, region and table; keep identifiers private |
| Collection model | Event-driven, continuous heartbeat, or bounded test; expected quiet periods |
| Schema | Version, required fields, timestamp semantics, sample redaction and rejected inputs |
| Normalization | Source-to-target mapping, ASIM alignment and limitations |
| Capacity | Events/day, serialized and expected billable bytes, maximum run/request size |
| Cost | Current regional meter, daily/total estimate, expiry, approval and stop conditions |
| Access | Exact principal, resource scopes, actions and data actions; separate provisioner/sender/query |
| Validation | Known event -> API receipt -> destination query -> unique IDs -> latency/quality |
| Recovery | Replay/duplicate handling, bounded retry policy, stopping collection without touching other sources |
| Acceptance | Evidence location, actual check time, unresolved blockers and sign-off |

An event-driven source with no events in one window has insufficient evidence of freshness; absence alone does not prove collection failure. Do not invent periodic heartbeats for Azure Activity or run administrative changes only to populate charts.
