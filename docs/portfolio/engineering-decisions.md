# Engineering decisions and trade-offs

These decisions explain the design's boundaries and alternatives. They are
implementation rationale, not claims that every alternative was deployed.

| Decision | Benefit | Cost / limit | Evidence or implementation |
|---|---|---|---|
| Reuse one existing workspace and subscription | Avoids duplicate infrastructure, licensing assumptions and tenant migration | No multi-tenant resilience or independent customer isolation is demonstrated | [Architecture](../architecture/overview.md) |
| Prefer local reproducible scenarios | Zero new Azure compute is needed; scenarios survive account closure | Synthetic behavior is not real attack/runtime validation | [RBA validation](../validation/phase-4.md) |
| Deploy disabled detection definitions | Verifies guarded control-plane delivery without silently activating recurring analytics | Provides no active protection or alert accuracy measurement | [Portfolio evidence](../validation/detection-portfolio.md) |
| Exact OIDC trust and exact resource grants | No permanent CI secret; limits which resource targets CI can write | RBAC cannot enforce disabled payloads or prevent all abuse of an authorized exact writer | [Security boundary](../security.md) |
| Fixed-contract bodies and approval fingerprints | Complete query/body/target changes are reviewable; arbitrary templates are rejected | Less flexible than a generic deployer; changing scope requires a new review | [Catalog contract](../../portfolio/catalog.py) |
| Actual REST read-back after deployment | Separates request acceptance from persisted state | A matching configuration does not prove data arrival or scheduled execution | [Actual OIDC AMA proof](../../evidence/local-linux-ama/oidc-configuration.sanitized.json) |
| Keep ambiguous Caller values as context | Avoids inventing canonical account identity from heterogeneous claims | Analysts need additional identity evidence; Account coverage is intentionally limited | [Detection catalog](../detections/portfolio.md) |
| Preserve original event IDs and reject conflicts | Prevents retry inflation and unsafe evidence overwrite | Upstream sources must provide a stable lineage contract | [RBA engine](../../rba/engine.py) |
| Distinct-event burst plus ordered cross-event correlation | Goes beyond isolated management events and retains provenance | Fixed bins have boundaries; same RG is contextual rather than proof of causal privilege use | [AZ-DET-011](../detections/AZ-DET-011.md), [AZ-DET-012](../detections/AZ-DET-012.md) |
| Separate health from risk | Missing telemetry affects confidence without discarding observed behavior | Overall health can remain Unknown even when configuration checks pass | [Health design](../operations/platform-health.md) |
| Use one reserved local4 Warning pilot | Tiny, specific Syslog transport test without university logs | Does not collect native SSH, authpriv, endpoint process or Windows/Sysmon events | [AMA validation](../validation/local-linux-ama.md) |
| Preserve batch/bootstrap ledgers | Avoids duplicate spend and repeated administrative exceptions | Ambiguous outcomes require investigation rather than convenient automatic retries | [AMA runbook](../onboarding/local-linux-ama.md) |
| Treat background automation as explicit scope | Avoids an unbounded recurring workload after the demonstration | Live continuous service is not demonstrated by a manual bounded pilot | [Customer assurance](../../customer/atlas-financial/service-assurance.md) |
| Use local case orchestration with human decisions | Exercises intake, failure recovery and investigation without paid SaaS or destructive actions | A simulated decision is not real Azure authorization or a closed Sentinel incident | [Operations](../../customer/atlas-financial/operations.md) |
| Publish evidence classes and unexecuted gates | A reviewer can audit what was measured | The result may be less dramatic than an unsupported “production complete” claim | [Project status](../PROJECT_STATUS.md) |

The architecture can be extended, but source expansion, runtime activation,
additional roles or recurring paid services are changes to operational scope.
They are not routine cosmetic improvements or implied by a small cost estimate.
