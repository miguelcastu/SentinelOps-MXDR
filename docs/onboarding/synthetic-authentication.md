# Synthetic authentication onboarding: Phase 2

**Implemented and tested offline. Not deployed, no events sent to Azure.** Atlas Financial is a fictional customer. Events imitate Windows authentication codes; they are not Windows Security Events collected from a host.

## Reproduce without Azure

```powershell
python -m ingestion
python -m unittest discover -s tests -v
python -m scripts.assess_detections
```

The default command writes source events, normalized events and an aggregate receipt into ignored `.local/ingestion-demo/`. It makes zero network requests and does not read credentials. The default dataset is fixed for reproducibility. An eventual live sender must generate current UTC timestamps and use the same batch manifest for validation.

`--count` accepts 1 through 100; the byte budget is an additional restriction. `--start` requires an explicit offset, and `--seed` accepts a short non-sensitive label. Same seed and start preserve batch/event IDs across retries. Changing the start or seed creates a different batch.

## Data contract and normalization

[Source schema](../../schemas/synthetic-auth.schema.json), [runtime validator and normalizer](../../ingestion/events.py), and [source inventory](../../ingestion/sources.json) are versioned. Runtime validation additionally limits IP addresses to documentation ranges. Missing fields, unknown fields, schema evolution, ambiguous timestamps, real usernames, unsupported codes and duplicate source IDs are rejected before any POST.

| Source | Normalized destination | Meaning |
|---|---|---|
| `timestamp` | `TimeGenerated`, `EventStartTime`, `EventEndTime` | Original event time converted to UTC milliseconds; not collector time |
| `event_code` | `EventOriginalType`, `EventResult` | 4624 -> Success; 4625 -> Failure; `EventType=Logon` |
| `event_id` | `EventOriginalUid` | Stable synthetic ID for reconciliation |
| `hostname` | `Dvc`, `DvcHostname` | Fictional reporting device |
| `username` | `TargetUsername` | Fictional authentication identity |
| `source_ip` | `SrcIpAddr` | Documentation IPv4/IPv6 only |
| `synthetic`, `batch_id` | `Synthetic`, `BatchId` | Explicit synthetic labeling and batch isolation |
| Generator constants | `EventCount`, vendor/product/schema/version, `CustomerName` | EventCount=1; fictional Atlas Financial |

Names follow the [ASIM Authentication schema](https://learn.microsoft.com/en-us/azure/sentinel/normalization-schema-authentication). This is an ASIM-shaped lab projection, **not** a registered `_Im_Authentication` parser or a claim of full ASIM compliance. Conditional username/entity typing and parser registration remain future integration work. Azure Activity remains a separate management-plane source.

## Proposed minimum Azure design

Existing workspace -> one new Analytics custom table `SentinelOpsAuth_CL`; one `kind=Direct` DCR `dcr-sentinelops-synthetic-auth` in West Europe -> that table. No VM, agent, DCE, new workspace, paid automation, private endpoint or schedule. The [DCR](../../infrastructure/ingestion/dcr.template.json) and [table](../../infrastructure/ingestion/table.json) are REST request bodies, **not ARM deployment templates**. [Offline configuration checks](../../ingestion/config.py) enforce matching schemas and one fixed destination. `configuration(pinned_workspace_id)` renders bodies in memory; it does not deploy.

The DCR uses an identity transform (`source`): normalization happens locally, so table and stream schemas are identical. A Direct DCR supplies a logs ingestion endpoint without a DCE when private link is unnecessary. This follows Microsoft's [Logs Ingestion API configuration](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/logs-ingestion-api-overview).

## Transport behavior

[Python client](../../ingestion/client.py) implements the real HTTPS POST transport, exercised here with mocks. It does not acquire credentials or create resources. No live workflow or CLI sender is enabled in this phase. A future approved integration must use OIDC, verify the pinned subscription and exact DCR destination through Azure GET, acquire an in-memory token for `https://monitor.azure.com`, and invoke the client. The client requires explicit approval, a West Europe ingestion hostname, the DCR immutable ID and the fixed stream name.

| Guard | Local limit |
|---|---|
| Events/run | 100 maximum; default 24 |
| Serialized normalized bytes/run | 65,536 maximum |
| Batch | 25 rows and 16,384 bytes maximum, including JSON delimiters |
| HTTP requests | 24 maximum; actual batch count x 3 must fit before sending |
| Attempts/batch | 3 maximum; retries only HTTP 429/500/502/503/504 |
| Backoff | 1 then 2 seconds, respect larger Retry-After up to 10 seconds; stop if longer |
| Rate | At least 1 second between request starts within one sender invocation |
| HTTP timeout | 20 seconds/request, TLS 1.2 minimum; redirects prohibited |

No raw response, URL, identity, token or event values are logged. A 401/403, redirect or malformed input stops immediately. A transport timeout has uncertain acceptance, so automatic retry stops. Explicit retryable HTTP failures may still cause duplicates; Azure ingestion is **not exactly once**. Inspect unique `EventOriginalUid` counts before replaying. Each invocation is bounded; no cross-run quota or global rate limiter is claimed.

Successful HTTP 204 means API acceptance, not verified table storage. The receipt always sets `destination_query_verified=false`. The [validation KQL](../../ingestion/validation.kql) must run separately after approval: exact batch, one-hour window, counts, unique IDs, invalid fields, duplicates, latency and billed bytes. It has **not executed in Kusto**. Replace the batch placeholder using the private manifest, require 24 unique events, 8 failures and 16 successes, and investigate any duplicate/invalid/negative-latency rows. Permit at most three queries at 5-minute intervals; stop after 15 minutes, document ingestion delay and do not resend automatically.

## Permissions and approval boundary

Existing CI keeps its current three custom roles and four assignments. No role was broadened. Before any cloud work, obtain approval for:

1. Provisioning: a separate narrowly scoped OIDC provisioner with table read/write **only at the exact new table URI**, DCR read/write **only at the exact new DCR URI**, and existing workspace read. Verify support for new-resource child scopes before relying on them; if Azure rejects them, return a revised proposal rather than widen to the workspace/group. No deletes, billing, diagnostics, retention or daily-cap writes. No generic ARM deployment permissions are needed for direct REST PUTs. Creating an identity/trust or RBAC assignments also requires explicit administrative authorization.
2. Sending: separate OIDC sender with DCR read plus `Microsoft.Insights/Telemetry/Write` data action at that DCR only. Microsoft's tutorial explicitly permits this custom data action instead of the broader Monitoring Metrics Publisher role. Do not add it to the existing detection CI identity implicitly.
3. Verifying: separately approved granular RBAC with a condition allowing data only from `SentinelOpsAuth_CL`, validated against Azure's current query authorization model. The legacy `Tables.Custom/read` permission grants all custom tables and is not acceptable as a substitute. No workspace-wide data access by default. See Microsoft's [table access guidance](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/manage-table-access). Azure Activity and incident access for Phase 1 are a different approval.
4. One 24-event run, no schedule, a conservative run estimate below EUR 0.01 (see [cost evidence](../validation/phase-1-2.md)), and current subscription/credit revalidation immediately before deployment. This is an estimate, not a billing guarantee or an authorization already granted.

After approval, build/review the gated workflows and authorize their exact OIDC subjects before deploying; the current deployment allowlist remains only the two disabled detections. Create the table before the DCR, check exact persisted configuration, send once, then validate. Re-running provisioning must inspect existing state and stop on mismatches rather than overwrite another owner's resources. Live provisioning/idempotency remains unverified until this authorized implementation exists.

## Troubleshooting and stopping

| Symptom | Action |
|---|---|
| 400 / schema mismatch | Compare stream, table and local column types; do not retry malformed events |
| 401 / 403 | Check monitor token audience and exact DCR data-action assignment; no permission escalation |
| 429 | Honor Retry-After; stop above local wait limit |
| Timeout / partial batch failure | Reconcile accepted unique IDs before any manual retry |
| 204 but no table rows | Check DCR output stream, destination, time window and initial ingestion latency; bounded queries only |
| Duplicate rows | Preserve raw evidence privately; deduplicate downstream by original event ID |

Stop the sender and leave it unscheduled. Do not alter Azure Activity export or remove its permissions. This offline phase needs no Azure rollback. If cloud provisioning is later approved, resource deletion and role removal must follow the separately approved cleanup scope; deleting a table alone does not immediately eliminate stored-data retention charges.
