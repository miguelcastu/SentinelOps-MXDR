# Discovery and security requirements

**Fictional customer workshop.** Example answers describe the lab design;
unanswered business facts remain questions rather than invented evidence.

## Discovery worksheet

| Question to the customer | Lab answer / required decision | Acceptance impact |
|---|---|---|
| Which legal entity, geography and data owners authorize monitoring? | Fictional Atlas Financial; real operator owns the personal lab. Customer approvals are simulated. | No real organization's data may be collected by this package. |
| Which assets support critical business functions? | Lab workspace and its Azure control plane; no real payment or customer platform is claimed. | Business impact cannot be inferred from a resource name. |
| Who owns the Azure subscription and tenant? | Existing pinned subscription; tenant ownership is outside this lab's authority. | Preserve subscription; do not onboard university directory telemetry. |
| Which sources are available and licensed? | Historical AzureActivity and bounded local Linux Syslog proof; authentication/endpoint formats are synthetic. | No Entra, Defender or M365 entitlement is assumed. |
| What principal formats occur? | AzureActivity Caller may be an application claim, object identifier or user-like value. | Do not automatically map every Caller to an Account. |
| Which administrative changes are normal? | Policy remediation, approved CI/RBAC setup and maintenance can match. | Exceptions need exact scope, operation, actor and expiry. |
| Are telemetry gaps acceptable during maintenance? | The personal VM is intentionally stopped between approved sessions. | Stopped VM is maintenance context, not proof of broken collection. |
| What response authority is delegated? | Investigation recommendations and local simulated case decisions only. | No automatic disable, isolation, deletion or containment. |
| Who can approve a sensitive change? | Lab operator; customer role in exercises is fictional. | Analyst and approver decisions must be recorded separately. |
| What are the communication and escalation routes? | Role-based exercise routes only; no real external recipient configured. | Do not send email, chat or page a real person. |
| What are retention, residency and data-minimization obligations? | Existing West Europe workspace, 30-day retention, unchanged. No regulatory certification is claimed. | New data classes require privacy/retention review. |
| What is the spending envelope and end date? | Limited promotional credit; existing spending limit/cap must remain. | Recheck actual eligibility and cost before any cloud work. |
| What is required for acceptance? | Reproducible demonstrations and evidence-class separation; actual cloud claims need actual responses. | A mock result cannot close a live cloud acceptance gate. |
| Who supports the service out of hours? | Nobody is committed to real coverage. | Exercise response targets are not contractual commitments. |
| How will the lab be offboarded? | Export safe portfolio evidence first; operator handles account closure using the handover checklist. | No automatic cancellation, deletion or billing upgrade. |

## Requirements register

| ID | Requirement | Verification |
|---|---|---|
| AF-SEC-01 | Keep the current subscription, spending protections and workspace controls. | Private pin comparison; actual sanitized financial/preservation evidence. |
| AF-SEC-02 | Use no permanent CI client secret and restrict deployable scope. | Exact OIDC subject, main-only environment, role/assignment audit and guarded payloads. |
| AF-SEC-03 | Preserve source events and separate canonical entities from ambiguous claims. | RBA lineage, join/conflicting-duplicate tests, documented AzureActivity entity limits. |
| AF-SEC-04 | Treat approved changes as investigation context, not blanket exclusions. | Narrow maintenance fixture and suspicious-lookalike regression controls. |
| AF-SEC-05 | Require an explicit human decision for consequential response. | Case decision/audit workflow; no containment adapter. |
| AF-SEC-06 | Keep tenant IDs, raw events, credentials and personal identities out of public artifacts. | Evidence allowlist, ignored private state, staged privacy review. |
| AF-REL-01 | Distinguish unknown health from healthy zero-volume event-driven sources. | Source policies, safe fault scenarios and explicit telemetry/runtime Unknown. |
| AF-REL-02 | Make intake/retry/recovery bounded and replay-safe. | Case duplicate/conflict controls and failure/recovery demonstrations. |
| AF-REL-03 | Keep validation reproducible without Azure. | Python offline CLIs, unit tests and public-repository CI. |
| AF-OPS-01 | Carry every change through source control and the protected PR path. | Required offline check on exact head; normal protected merge. |
| AF-OPS-02 | Tie every closure to evidence, verdict, limits and an owner. | Structured case/ticket fields and investigation template. |
| AF-OPS-03 | Allow a successor to reproduce the demonstration after account closure. | Offline demo, evidence manifest, recovery and handover runbooks. |

The lab does not establish compliance with PCI DSS, DORA, GDPR or any other
framework. A real financial customer would require a separate legal, privacy,
residency, licensing and operating-model review before collection begins.
