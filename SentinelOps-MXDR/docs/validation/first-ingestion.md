# First real ingestion: evidence and limitations

Snapshot: 13 October 2026. The source screenshots were provided by the lab operator and sanitized before inclusion.

| Observation | Value |
|---|---:|
| Azure Policy remediation | Complete, **1 of 1** resources |
| Export diagnostic setting | `subscriptionToLa` → Log Analytics in West Europe |
| Events returned by last-24h KQL summary | **9** |
| Distinct `Caller` values | **3** |
| Earliest / latest result UTC | **20:27:23.329 / 20:31:28.280** |
| Mean estimated ingestion delay | **7.89 minutes** |
| Max estimated ingestion delay | **9 minutes** |

The `ingestion_time()` function returns an approximate ingestion timestamp; `datetime_diff("minute",...)` produces integer-minute results. These numbers are a small sample, **not a production latency baseline or SLA**. `dcount(Caller)` indicates distinct caller values, not necessarily distinct humans.

The operation grouping includes resource deployments, diagnostic-settings writes, a policy deployment action and remediation writes. Statuses included Success, Start, Accept and a Failure event, notwithstanding the final successful remediation task.

### Screenshots

- [Azure resources](../../evidence/01-azure-resources.png)
- [Connector inventory](../../evidence/02-azure-activity-connector.png)
- [Policy assignment](../../evidence/03-azure-policy-assignment.png)
- [Remediation 1/1](../../evidence/04-remediation-complete.png)
- [Diagnostic destination](../../evidence/05-diagnostic-settings.png)
- [KQL summary](../../evidence/06-kql-ingestion-summary.png)
- [Operation distribution](../../evidence/07-kql-administrative-operations.png)
- [Ingestion latency](../../evidence/08-kql-ingestion-latency.png)

**UI caveat:** the connector inventory image shows Azure Activity without an unambiguously green connected badge; the data pipeline was established independently using diagnostic settings plus actual ingested events. We should investigate any UI status mismatch later rather than claiming that badge is connected.
