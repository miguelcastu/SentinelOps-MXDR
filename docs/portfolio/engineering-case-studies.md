# Troubleshooting case studies

Actual observed engineering cases are labeled below. Timelines and public
counts come from existing sanitized validation records; private identities,
tokens and raw telemetry are deliberately omitted.

## 1. Policy assigned, existing subscription still not exporting

**Actual lab operation.** A correct-looking Azure Policy assignment did not
immediately configure the pre-existing subscription. Inspecting assignment
scope, effect, destination and compliance led to a remediation task. The task
reported **1/1 resources remediated**; subscription diagnostic export and
actual AzureActivity rows then established delivery. A neutral connector badge
alone was insufficient evidence either way.

**Lesson:** separate governance intent, remediation execution, destination
configuration and actual queried data. Do not create a second exporter simply
because a connector UI is ambiguous.

[Original troubleshooting](../troubleshooting/azure-policy-remediation.md),
[actual ingestion record](../validation/first-ingestion.md).

## 2. Least-privilege RBAC could not target an absent DCR

**Actual lab operation.** Azure CLI scope resolution and then direct ARM
role assignment returned HTTP 404 `ResourceNotFound` for the not-yet-existing
DCR. Repeating the exact-scope request confirmed the boundary. Granting a
resource-group writer would have weakened the design, so execution stopped.

The operator approved a specific one-time personal MFA initialization for
only DCR, AMA extension and association. Once they existed, exact assignments
were attached to the existing CI identity and main OIDC verified all three
as already matching. The bootstrap completion ledger remains consumed.

**Lesson:** an explicit, reviewed first-creation exception can solve a real
platform boundary without turning a narrowly scoped routine deployer into
a generic infrastructure administrator. The personal bootstrap must not be
misreported as OIDC creation.

[Actual RBAC blocker](../../evidence/local-linux-ama/rbac-boundary.sanitized.json),
[approved exception](../deployment/ama-bootstrap-exception.md),
[OIDC verification](../../evidence/local-linux-ama/oidc-configuration.sanitized.json).

## 3. DCR write succeeded but strict read-back rejected Azure metadata

**Actual lab operation.** Azure added a read-only destination `workspaceId`
to the GET representation. The initial complete-object comparison stopped
after creation. The protected fix accepted that documented response shape
only when the value matched independently read existing-workspace metadata;
wrong IDs, extra destinations and unknown fields still failed.

**Lesson:** strict request/response comparison needs a narrowly modeled
read-only schema. Dropping every unknown field would have hidden real drift;
blind equality would have rejected a valid platform response forever.

[Validation and PR #18 history](../validation/local-linux-ama.md),
[comparison implementation](../../ama/cloud.py).

## 4. AMA installation progressed beyond the client's bounded wait

**Actual lab operation.** A roughly 606 MB package downloaded/unpacked slowly
on a one-vCPU guest. A bounded polling window expired; an immediate extension
GET also briefly returned HCRP404. Private local diagnostics and later actual
REST showed the existing operation continuing. The same resource was resumed
and eventually verified Succeeded without another creation request, a larger
paid machine or broader permissions.

The DCR association appeared after AMA's first configuration request, so the
local4 config was initially absent. A targeted guest-service restart refreshed
configuration; the pilot waited for the downloaded DCR before sending.

**Lesson:** timeout is an observation boundary, not proof that the asynchronous
resource is absent. Inspect the existing operation before retrying a mutation.

[Actual AMA troubleshooting](../validation/local-linux-ama.md).

## 5. First query returned zero; resending would have been wrong

**Actual lab operation.** One ten-message batch was sent at roughly 21:50 UTC.
The first aggregate query at 21:52:01 returned zero. Local forwarding and AMA's
listener were healthy. The second permitted query at 21:55:02 returned ten
total and ten distinct events, **2,600 billable bytes**. No second batch or
third query was required; the guest was gracefully shut down afterwards.

**Lesson:** reconcile a stable run identifier and respect the consumed sender
ledger. Delayed ingestion is not permission to duplicate the workload. The
900-byte payload also illustrates that message bytes differ from billable
event size and final monetary charges.

[Actual Kusto aggregate](../../evidence/local-linux-ama/ingestion.sanitized.json),
[actual shutdown](../../evidence/local-linux-ama/shutdown.sanitized.json).

## 6. Benign maintenance resembled a multi-stage compromise

**Synthetic control scenario.** The fictional dataset includes authentication,
role, diagnostic and endpoint-style events for a maintenance actor. A narrow
event-time exception binds the correct actor, source, operation/scope and
validity, reducing its contribution while preserving evidence. Wrong-order,
wrong-host, wrong-scope and shared-IP/different-account controls do not produce
the demonstrated attack finding.

**Lesson:** tune the evidence relationship and bounded business context;
do not whitelist a privileged identity or erase all activity during maintenance.
These controlled scenarios do not measure production false-positive rates.

[RBA design](../operations/risk-correlation.md),
[synthetic validation](../validation/phase-4.md).

## 7. Closing an incident changed its activity timeline

**Actual lab operation.** The dedicated synthetic test produced one scheduled
alert and a linked incident. OIDC successfully classified it Closed /
BenignPositive / SuspiciousButExpected at **19:33:13 UTC**. The closure PUT
omitted optional first/last activity fields; later metadata inspection showed
that the incident no longer retained the verified **19:12:41** source time.

The correction preserved activity fields in closure payloads and added an
explicit reconciliation bound to this exact already closed incident and
query digest. The original snapshot, recorded at **19:23:01**, the fixed query
and actual alert independently supported the timestamps. [OIDC run
41709469491](https://github.com/miguelcastu/SentinelOps-MXDR/actions/runs/41709469491)
restored them through **one exact-incident PUT** and verified the result at
**20:07:05**. Classification stayed unchanged. No new event, activation,
ingestion or additional permission was needed. The final preservation audit
then passed 76 checks, including two timeline checks at **20:10:19**.

**Lesson:** a successful PUT can have unintended effects when optional fields
are omitted. Preserve verified metadata and compare the full managed contract
after a write. Repair from independent source evidence; do not invent replacement
timestamps or repeat the event to produce a cleaner screenshot. The final
reconciliation was a write followed by verification, distinct from the GET-only
infrastructure verifier and metadata-only observer.

[Full lifecycle and authority](../validation/lifecycle.md),
[actual reconciliation](../../evidence/completion/lifecycle-start.sanitized.json),
[original classification](../../evidence/completion/lifecycle-close.sanitized.json),
[final preservation audit](../../evidence/completion/final-preservation.sanitized.json).
