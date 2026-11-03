# Atlas Financial: fictional MXDR service package

**Atlas Financial is fictional.** These are engineering and operating artifacts
for a personal Microsoft Sentinel laboratory, with no real customer,
commercial service contract, staffed SOC or affiliation with a security vendor.
Proposed service targets below are exercise parameters, not measured SLAs.

The package combines twelve versioned AzureActivity detection definitions,
restricted GitHub OIDC delivery, source-health analysis, synthetic multi-stage
risk correlation and a local case-management demonstration. Historical actual
cloud evidence is linked explicitly; a synthetic case is never represented as
a Sentinel incident.

| Operational question | Artifact |
|---|---|
| What must we learn before accepting a customer? | [Discovery and requirements](discovery-requirements.md) |
| What is monitored, by whom, and through which data paths? | [Service design and RACI](service-design.md) |
| What can the detections observe, and what can they miss? | [Coverage matrix](detection-coverage.md), [machine-readable catalog](coverage.json) |
| How does an analyst triage, investigate, escalate and tune? | [Operations and change control](operations.md) |
| What do we measure and what risks are accepted? | [Service assurance](service-assurance.md) |
| How does another engineer operate, recover or close the lab? | [Handover and closure](handover.md) |
| What would realistic service work look like? | [Eight service tickets](service-tickets.md), [structured records](service-tickets.json) |
| Which deliverables exist and which acceptance gates remain? | [Acceptance contract](acceptance.json), [validation](../../docs/validation/customer-operations.md) |

## Evidence boundary

The baseline has twelve managed **disabled** scheduled rules plus the original
enabled Fusion rule outside managed scope. Disabled definitions provide no
active alerting. Their most recent published preservation proof is the
[28 October REST/RBAC audit](../../evidence/local-linux-ama/preservation.sanitized.json).
The [AMA pilot](../../evidence/local-linux-ama/ingestion.sanitized.json) reconciled
ten total / ten distinct messages and 2,600 billable bytes; the [guest was then
stopped](../../evidence/local-linux-ama/shutdown.sanitized.json). This is a dated
proof of transport, not current telemetry freshness or native SSH coverage.

The project's [current status](../../docs/PROJECT_STATUS.md) is authoritative
for later cloud observations. This customer package does not assert a real
scheduled-rule alert/incident lifecycle; that needs its own actual evidence.
No production precision, response-time performance or attack-prevention claim
can be derived from synthetic demonstrations.

## Verify the package offline

From the repository root:

```powershell
python customer/atlas-financial/validate.py
```

The validator compares all twelve coverage records to the versioned rule
bodies, validates ticket fields and scope, checks twenty customer deliverables
and their evidence links, and rejects missing/unrecognized acceptance states.
It makes no Azure request, starts no VM and creates no customer account.

Use the [five-minute demo](../../docs/portfolio/demo-five-minutes.md) for a hiring
panel and the [technical presentation](../../docs/portfolio/presentation-fifteen-minutes.md)
for an engineering interview. Neither requires an active Azure subscription.
