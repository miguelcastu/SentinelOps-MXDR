# Eight fictional MXDR service tickets

**Every ticket below is a fictional exercise**, not a real service/customer
request or a claim that someone was paged. References may cite actual historical
lab evidence, but the ticket identity, priority and closure are simulated.
`ClosedSynthetic` explicitly distinguishes these records from actual Sentinel
incidents. [Structured records](service-tickets.json) are validated offline.

## AF-SVC-001: Accept one owned Linux source

Category: `source-onboarding`. Exercise priority: P3. Status: **ClosedSynthetic**.

**Trigger:** The fictional customer asks to demonstrate Linux log onboarding without using a managed university endpoint or an Azure VM.

**Investigation:**

1. Confirm ownership, collection facility/severity, one existing destination and explicit finite pilot consent.
2. Verify actual Arc machine, AMA extension, exact DCR and association independently from the local package installation.
3. Reconcile only the approved run with aggregate count/distinct/billable bytes; preserve the consumed ledger.

**Root cause / interpretation:** A collector package alone cannot establish destination delivery; acceptance must follow the complete approved data path.

**Actions and acceptance:**

- Use the fixed one-machine Arc/AMA design and exact resource-scoped access.
- Record ten expected unique labeled messages and their verified destination counts.
- Stop the owned local guest after the bounded verification.
- Counts reconcile ten total / ten distinct for the historical lab pilot.
- Actual shutdown read-back shows poweroff and the existing DCR remains unchanged.

**Closure:** ClosedSynthetic: the fictional onboarding acceptance exercise follows actual historical transport and shutdown evidence; no new upload was sent.

**Limitations:** The actual evidence is historical, not current source freshness. Only local4 Warning and higher is selected; native SSH/authpriv is not covered.

References: [docs/onboarding/local-linux-ama.md](../../docs/onboarding/local-linux-ama.md), [evidence/local-linux-ama/ingestion.sanitized.json](../../evidence/local-linux-ama/ingestion.sanitized.json), [evidence/local-linux-ama/shutdown.sanitized.json](../../evidence/local-linux-ama/shutdown.sanitized.json).

## AF-SVC-002: Policy exists but no rows are visible

Category: `connector-troubleshooting`. Exercise priority: P2. Status: **ClosedSynthetic**.

**Trigger:** A fictional operator sees a neutral connector badge after assigning Azure Activity export policy and assumes onboarding has failed.

**Investigation:**

1. Verify assignment at subscription scope, destination workspace and logsEnabled/effect parameters.
2. Inspect compliance and remediation state for the already-existing subscription.
3. Verify the resulting diagnostic export and bounded actual destination summary rather than trusting the connector badge.

**Root cause / interpretation:** In the historical engineering case, the existing subscription needed remediation after policy assignment; a UI badge was not delivery evidence.

**Actions and acceptance:**

- Use the policy remediation path rather than creating a duplicate export.
- Record the expected destination and actual query window separately from UI status.
- Historical remediation evidence records one of one resources complete.
- Historical AzureActivity summary contains actual records in the correct workspace.

**Closure:** ClosedSynthetic: the fictional connector ticket is resolved using the documented diagnostic method and dated real lab evidence, without modifying collection.

**Limitations:** No current AzureActivity freshness query is executed by this ticket. A populated historical sample does not prove every category or future availability.

References: [docs/troubleshooting/azure-policy-remediation.md](../../docs/troubleshooting/azure-policy-remediation.md), [docs/validation/first-ingestion.md](../../docs/validation/first-ingestion.md).

## AF-SVC-003: Approved role grant matches a detection

Category: `detection-tuning`. Exercise priority: P3. Status: **ClosedSynthetic**.

**Trigger:** An approved maintenance role grant produces the same control-plane behavior the fictional analyst is investigating as a suspicious change.

**Investigation:**

1. Inspect original event ID, actor format, exact target scope, role permissions and change approval.
2. Compare the authorized action with a suspicious lookalike outside the approved scope or time window.
3. Preserve the matching event and document benign-positive reasoning instead of calling every authorized match a logic defect.

**Root cause / interpretation:** The detection is a behavioral signal; legitimate administration can correctly satisfy its predicates.

**Actions and acceptance:**

- Bind any maintenance exception to actor, operation, target, source and expiry.
- Add positive, benign-lookalike and out-of-scope controls before proposing a protected tuning change.
- Approved maintenance is explained while the suspicious lookalike remains observable.
- No blanket CI/admin allowlist or silent live activation is introduced.

**Closure:** ClosedSynthetic: the example is classified as benign positive with a narrow proposed tuning control; no production false-positive rate is inferred.

**Limitations:** Synthetic fixtures are not real operational accuracy data. The twelve managed AzureActivity rules remain disabled.

References: [docs/detections/lifecycle-validation.md](../../docs/detections/lifecycle-validation.md), [docs/operations/risk-correlation.md](../../docs/operations/risk-correlation.md), [tests/fixtures/detection_triage.json](../../tests/fixtures/detection_triage.json).

## AF-SVC-004: Investigate a multi-stage fictional compromise

Category: `incident-investigation`. Exercise priority: P1. Status: **ClosedSynthetic**.

**Trigger:** A synthetic authentication sequence is followed by a role grant, diagnostic change and endpoint-style execution for one canonical account.

**Investigation:**

1. Verify canonical mapping and original-event lineage before linking stages.
2. Check strict time order and matching host/resource context; reject a shared-IP-only identity join.
3. Inspect contribution caps/decay and record Unknown endpoint-health confidence limits.

**Root cause / interpretation:** The fictional sequence satisfies AF-RBA-001; the finding prioritizes investigation and is not proof of a real compromise.

**Actions and acceptance:**

- Create or locate the idempotent local case and attach the evidence chain.
- Record analyst interpretation, explicit human decision and evidence-backed synthetic classification.
- Preserve residual collection gaps and follow-up actions in the audit.
- The synthetic finding retains all source event IDs and ordered stage context.
- The local case audit distinguishes recommendation, approval and final classification.

**Closure:** ClosedSynthetic: the fictional case is investigated and classified using labeled evidence; no real Sentinel/Defender incident closure is claimed.

**Limitations:** No actual endpoint attack or security containment is executed. The original mission live Sentinel lifecycle remains a separate acceptance gate.

References: [docs/operations/risk-correlation.md](../../docs/operations/risk-correlation.md), [evidence/phase-4/risk-report.synthetic.json](../../evidence/phase-4/risk-report.synthetic.json), [customer/atlas-financial/operations.md](../../customer/atlas-financial/operations.md).

## AF-SVC-005: Required validation blocks an unsafe payload

Category: `pipeline-failure`. Exercise priority: P2. Status: **ClosedSynthetic**.

**Trigger:** A fictional detection change adds an extra destination, arbitrary query or enabled state outside the reviewed fixed contract.

**Investigation:**

1. Reproduce the contract failure offline and inspect the changed properties.
2. Confirm validation runs before OIDC authentication and deployment.
3. Check that no cloud success evidence is emitted from the failing mock/local test.

**Root cause / interpretation:** The proposed payload violates an explicit allowlisted contract; the block is intended behavior, not a deployment outage to bypass.

**Actions and acceptance:**

- Correct the payload or propose a separate reviewed scope change.
- Retain negative regression controls and require exact-head offline CI before normal merge.
- The unsafe change fails locally/CI before cloud mutation.
- The corrected fixed contract passes required validation without bypassing branch protection.

**Closure:** ClosedSynthetic: the fictional pipeline request is corrected through the protected path; no broad writer or environment bypass is used.

**Limitations:** A passing offline test is not actual Azure deployment proof. No failing scenario is injected into live collection.

References: [tests/test_ama_cloud.py](../../tests/test_ama_cloud.py), [tests/test_deployment.py](../../tests/test_deployment.py), [.github/workflows/validate.yml](../../.github/workflows/validate.yml), [docs/security.md](../../docs/security.md).

## AF-SVC-006: Demonstrate safe local case orchestration

Category: `automation-deployment`. Exercise priority: P3. Status: **ClosedSynthetic**.

**Trigger:** The fictional SOC asks for automatic enrichment and case tracking while retaining human authority over consequential response.

**Investigation:**

1. Validate intake evidence class, stable finding identity and source lineage.
2. Exercise duplicate and conflicting delivery, bounded adapter failure and recovery.
3. Check that a pending or denied human decision cannot become an executed containment action.

**Root cause / interpretation:** The requested workflow can be demonstrated with local state and audit records; no paid Logic App, SaaS or real containment is necessary.

**Actions and acceptance:**

- Use the local synthetic case integration and deterministic context.
- Record state transitions and explicit decision/audit entries.
- Export the exercise result with fiction labels and response limitations.
- A finding reaches a reproducible investigated/classified local case state.
- Identical replay is idempotent and conflicting evidence is rejected.
- No cloud notification, account disable, resource deletion or paid service occurs.

**Closure:** ClosedSynthetic: the local orchestration exercise is accepted with persistent evidence and human gates; actual Azure incident automation remains separate.

**Limitations:** A simulated approval does not grant Azure authorization. A local closed case is not a closed Sentinel incident.

References: [customer/atlas-financial/operations.md](../../customer/atlas-financial/operations.md), [docs/PROJECT_STATUS.md](../../docs/PROJECT_STATUS.md).

## AF-SVC-007: Explain payload versus billed volume

Category: `cost-investigation`. Exercise priority: P2. Status: **ClosedSynthetic**.

**Trigger:** The fictional customer expects the billable volume to equal a 900-byte message payload and treats the credit balance as a real-time spending guarantee.

**Investigation:**

1. Compare message bytes with actual aggregate billable bytes from the same accepted run.
2. Record credit observation timestamp, expiry and the possibility of delayed usage posting.
3. Distinguish daily-cap/budget alerts from a guaranteed monetary ceiling.

**Root cause / interpretation:** Log metadata and billing semantics differ from message payload size; closed credit balances can lag usage.

**Actions and acceptance:**

- Report the historical pilot as 900 payload bytes and 2600 billable bytes.
- Leave final monetary charge unknown until billing provides it.
- Stop unnecessary repeat tests and preserve the existing spending and workspace controls.
- The report includes volume, time/evidence scope, expiry and billing uncertainty.
- No zero-charge promise, pricing change, subscription upgrade or new paid feature is introduced.

**Closure:** ClosedSynthetic: the cost explanation is corrected using actual historical volume evidence; no synthetic price is represented as an invoice.

**Limitations:** Final monetary charge is not established by billable-byte arithmetic alone. Existing unrelated workloads may still incur charges.

References: [evidence/local-linux-ama/ingestion.sanitized.json](../../evidence/local-linux-ama/ingestion.sanitized.json), [evidence/local-linux-ama/financial.sanitized.json](../../evidence/local-linux-ama/financial.sanitized.json), [customer/atlas-financial/service-assurance.md](../../customer/atlas-financial/service-assurance.md).

## AF-SVC-008: Investigate simulated workspace/rule drift

Category: `configuration-drift`. Exercise priority: P2. Status: **ClosedSynthetic**.

**Trigger:** A synthetic health observation differs from the reviewed workspace retention/cap or managed disabled-rule properties.

**Investigation:**

1. Compare only reviewed managed properties against the approved contract.
2. Separate configuration mismatch from unavailable telemetry and rule-runtime evidence.
3. Verify inventory completeness and target ownership before proposing a correction.

**Root cause / interpretation:** The simulated configuration differs from policy; this does not itself prove an actual Azure setting changed or that logging stopped.

**Actions and acceptance:**

- Preserve the synthetic faulty observation and expected values.
- Open a controlled exact-target change with before-state, rollback and post-read-back criteria.
- Run local fault controls without changing actual collection.
- The simulated scenario becomes Misconfigured with a specific reason.
- The baseline/control remains distinct from Unknown telemetry or a quiet source.
- No Azure retention, cap, pricing or diagnostic setting is altered by the demonstration.

**Closure:** ClosedSynthetic: the drift exercise identifies the mismatched contract and controlled remediation plan; no live fault or auto-repair was deployed.

**Limitations:** Configuration agreement does not prove runtime or data freshness. Actual remediation would require separately authorized scope and verification.

References: [docs/operations/platform-health.md](../../docs/operations/platform-health.md), [evidence/phase-3/fault-injection.sanitized.json](../../evidence/phase-3/fault-injection.sanitized.json), [platform_health/demo.py](../../platform_health/demo.py).
