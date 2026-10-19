# Detection portfolio validation

Checkpoint: 19 October 2026. This increment prioritizes detection breadth before Phase 5 SOAR. Scope: AZ-DET-003 through AZ-DET-012, all disabled, using existing AzureActivity; preserve AZ-DET-001/002 and Fusion, subscription plan and collection settings.

## Local evidence

- Ten complete fixed REST contracts and synchronized KQL files pass `python -m portfolio`; 60 explicit synthetic controls pass. These are Python reference simulations, not Kusto execution.
- 130 unit tests pass, including threshold/bin/time boundaries, actor/scope separation, latest ordered pair and tie handling, original-event replay/conflict handling, benign administration matches, missing lineage and the Azure entity-mapping requirement.
- Deployment fault tests reject missing/stale approval, personal sessions, enabled/drifted/template-managed/wrong-ID targets, duplicate/partial inventories and Azure errors before any write. Matching targets produce no PUT on re-run.
- Administrative setup tests verify exactly ten rule-scoped assignments using existing identity/trust/roles. Broad permissions, wrong trust and mismatched subscription pins stop setup before mutation. Preview has no Azure REST call or GitHub mutation.
- Existing two-rule validators pass. No original rule query, original deployment workflow or shared deployment guard is modified.

The [simulation evidence](../../evidence/detection-portfolio/simulation.synthetic.json) records the contract fingerprint and explicit limitations. No real-data precision/false-positive rate, fresh source telemetry, alert, incident, Kusto compile or guest execution is claimed. [Coverage and investigation runbooks](../detections/portfolio.md) distinguish potential coverage from populated source/resource evidence.

## Azure baseline and delivery

Fresh read-only Azure REST inventory on 19 October confirmed three initial rules: Fusion enabled, AZ-DET-001/002 disabled. No raw event or identity output was requested. Implementation [PR #10](https://github.com/miguelcastu/SentinelOps-MXDR/pull/10) merged as `4c12123` after [required Python 3.12 CI](https://github.com/miguelcastu/SentinelOps-MXDR/actions/runs/39235253199) passed. Administrative setup reused the identity/trust/three narrow roles and verified fourteen total assignments: the four existing assignments plus ten exact rule targets. No broader permission or query access was introduced.

The [first actual OIDC deployment](https://github.com/miguelcastu/SentinelOps-MXDR/actions/runs/39235429137) verified AZ-DET-003 through AZ-DET-010 disabled through PUT responses and GET readback. The job then stopped with Azure `BadRequest`: entityMappings length must be between one and five. AZ-DET-011's initially empty mapping was rejected; AZ-DET-012 was not attempted. That run was partial deployment, not success. The fix maps the actual subscription/resource-group context derived from event fields as AzureResource, without inventing an Account identity or assigning an arbitrary IP to an aggregate. A regression check enforces the API minimum; matching existing definitions require no write on the corrected run.

The mapping correction passed [required Python 3.12 CI](https://github.com/miguelcastu/SentinelOps-MXDR/actions/runs/39235750854) and merged through [protected PR #11](https://github.com/miguelcastu/SentinelOps-MXDR/pull/11) as `38f1627`. Administrative setup revalidated the same fourteen exact assignments without adding permissions and refreshed only the approved portfolio fingerprint.

The [second actual OIDC deployment](https://github.com/miguelcastu/SentinelOps-MXDR/actions/runs/39235924991) succeeded on that merge. At 19 October 2026 10:14:14 UTC it verified eight existing matching rules with no PUT, created AZ-DET-011/012 disabled, and verified all ten via final inventory. [Sanitized deployment evidence](../../evidence/detection-portfolio/deployment.sanitized.json) preserves the ten public UUIDs, per-rule result, fixed-contract fingerprint, commit and explicit execution limits. All managed properties match the reviewed source. There was no deletion or activation.

An independent personal-session read-only REST audit at 10:15:42 UTC confirmed **13 total rules: 12 managed scheduled definitions disabled and the pre-existing Fusion enabled**. AZ-DET-001/002 and Fusion properties equal the private pre-increment baseline. Same pinned subscription/tenant, West Europe workspace, `pergb2018`, 30-day retention and 0.1 GB daily cap. No Sentinel data-connector ARM resources exist; this does not remove or disprove the pre-existing diagnostic-export AzureActivity pipeline. The subscription export was neither read nor changed. [Sanitized preservation evidence](../../evidence/detection-portfolio/preservation.sanitized.json) records the audit and its limits; no personal-session rule write was performed.

Local Python 3.15 passed the complete 130-test suite. The managed local Python 3.12 installation could not load its SSL DLL because Windows Application Control blocked that file; the policy was preserved, and required GitHub Python 3.12 CI plus the actual deployment workflow passed all 130 tests instead. Actionlint, documentation links, whitespace and private-identifier/credential checks passed. Public-repository standard runners were used; no Azure data query was executed.

## Budget and source boundary

Reuse existing AzureActivity; no additional connector/source, paid component, diagnostic setting change, log query, incident, recurring workload, price/retention/cap/budget change or subscription switch is included. Existing Azure usage can still incur charges. The 18 October credit balance is historical, not a refreshed billing measurement. No credit consumption experiment is required to build this portfolio.
