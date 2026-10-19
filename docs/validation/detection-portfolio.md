# Detection portfolio validation

Checkpoint: 19 October 2026. This increment prioritizes detection breadth before Phase 5 SOAR. Scope: AZ-DET-003 through AZ-DET-012, all disabled, using existing AzureActivity; preserve AZ-DET-001/002 and Fusion, subscription plan and collection settings.

## Local evidence

- Ten complete fixed REST contracts and synchronized KQL files pass `python -m portfolio`; 60 explicit synthetic controls pass. These are Python reference simulations, not Kusto execution.
- 129 unit tests pass, including threshold/bin/time boundaries, actor/scope separation, latest ordered pair and tie handling, original-event replay/conflict handling, benign administration matches and missing lineage.
- Deployment fault tests reject missing/stale approval, personal sessions, enabled/drifted/template-managed/wrong-ID targets, duplicate/partial inventories and Azure errors before any write. Matching targets produce no PUT on re-run.
- Administrative setup tests verify exactly ten rule-scoped assignments using existing identity/trust/roles. Broad permissions, wrong trust and mismatched subscription pins stop setup before mutation. Preview has no Azure REST call or GitHub mutation.
- Existing two-rule validators pass. No original rule query, original deployment workflow or shared deployment guard is modified.

The [simulation evidence](../../evidence/detection-portfolio/simulation.synthetic.json) records the contract fingerprint and explicit limitations. No real-data precision/false-positive rate, fresh source telemetry, alert, incident, Kusto compile or guest execution is claimed. [Coverage and investigation runbooks](../detections/portfolio.md) distinguish potential coverage from populated source/resource evidence.

## Azure baseline and delivery

Fresh read-only Azure REST inventory on 19 October confirmed three rules: Fusion enabled, AZ-DET-001/002 disabled. No raw event or identity output was requested. Implementation delivery, exact permission preparation and actual portfolio deployment are pending at this checkpoint; local success is not deployment evidence.

Only approved GitHub Actions OIDC after protected PR merge can create the ten fixed disabled targets. Public sanitized deployment evidence will record actual PUT/GET/inventory verification, timestamp, matching properties and preservation of existing rules. A partial deployment must be reported as partial and must not be deleted or activated automatically.

## Budget and source boundary

Reuse existing AzureActivity; no additional connector/source, paid component, diagnostic setting change, log query, incident, recurring workload, price/retention/cap/budget change or subscription switch is included. Existing Azure usage can still incur charges. The 18 October credit balance is historical, not a refreshed billing measurement. No credit consumption experiment is required to build this portfolio.
