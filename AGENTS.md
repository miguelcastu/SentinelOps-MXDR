# SentinelOps MXDR agent instructions

Microsoft Sentinel engineering lab. Resource group: `rg-sentinelops-mxdr`.
Workspace: `law-sentinelops-mxdr-euw`, West Europe.

## Authorized work

- Develop KQL, detection definitions, Python tooling, tests and English documentation.
- Work on feature branches and prepare commits and pull requests.
- Deploy only through the approved GitHub Actions OIDC workflow after PR approval and merge.
- Verify deployment through the actual Azure REST response; distinguish local tests from cloud evidence.

## Subscription and cost constraints

- Preserve the existing Azure subscription and its plan. Never switch subscriptions or upgrade billing.
- On 18 October 2026, the credit API reported EUR 175.99436818021823 closed balance, expiry 12 November 2026 18:00:16 UTC. Reverify before any proposed paid component; published balances can lag usage.
- Prefer offline work and free public-repository standard GitHub runners. Do not consume credit for experiments.
- Never create VMs, databases, workspaces, connectors, Logic Apps, paid resources or Defender plans.
- Never change pricing, retention, ingestion, daily caps, budgets or diagnostic settings.
- The operator explicitly authorized administrative setup on 18 October 2026: reuse `id-sentinelops-ci`, configure narrow custom RBAC and exact GitHub OIDC trust, and populate GitHub environment identifiers. The personal session may be used for that setup and verification only, with valid MFA.
- Routine rule deployments must use GitHub OIDC, never the personal account. Do not create duplicate identities, grant broad roles, weaken MFA/Conditional Access or use Cloud Shell.
- Request human intervention only for unavoidable MFA/consent or sensitive changes outside the authorized scope. Continue independent work while authentication is pending.
- Never delete Azure resources or deploy unrelated infrastructure.

## Deployment boundary

- The operator subsequently explicitly approved the PR #16 exception on 28 October 2026: initialize only the same fixed DCR, AMA extension and association once using the pinned personal administrative MFA session, then finish exact-resource RBAC and GitHub OIDC verification. This supersedes OIDC-only first creation for those three targets only. `scripts/bootstrap_ama_resources.py` requires the separate private approval record and completion ledger. No broader role, extra source/batch or permanent personal deployment path is authorized. Routine operations remain on protected merged-main OIDC.

- On 28 October 2026 the operator explicitly authorized preparing one VM on this personal PC, then approved the concrete PR #13 Arc/AMA pilot: only `lab-sentinelops-linux-01`, one fixed DCR `dcr-sentinelops-ama-linux`, its `AzureMonitorLinuxAgent` extension and `sentinelops-ama-linux` association, narrow exact-target RBAC, the three missing Arc prerequisite providers, and one ten-message (<=4096 message bytes) pilot with bounded aggregate-only verification. This specific exception permits one-time local Arc administrative authentication using the pinned MFA session; DCR/extension/association deployment must still use protected merged-main GitHub OIDC. No Azure VM, university source/device join, add-on plan, pricing/cap/retention/diagnostic change, rule activation, long-lived secret, broader source or recurring workload is authorized. Stop the local guest after verification. Do not replay an ambiguous pilot or reset its attempt ledger automatically. Current contracts and approval fingerprint are in `ama/cloud.py`; prior bootstrap scripts may intentionally reject the added narrow AMA assignments.

- Update AZ-DET-001 only at its configured existing UUID.
- The operator authorized one additional disabled detection, AZ-DET-002 (Azure Role Assignment Created), on 18 October 2026. Its dedicated workflow may create/update only its fixed, reviewed UUID. No other resource creation is authorized.
- On 19 October 2026 the operator prioritized a larger detection portfolio before SOAR and requested implementation under the existing subscription/budget limits. This authorizes the ten fixed disabled AZ-DET-003 through AZ-DET-012 definitions in `portfolio/catalog.py`, reviewed and merged through the protected PR path, then manually deployed by `deploy-portfolio.yml` through existing OIDC. Its fingerprint must match the environment approval. Reuse the existing identity, trust and writer role with only ten exact rule assignments; no broad role, activation, incident creation, live query, paid component or additional source is included. This specific increment extends the earlier two-rule creation boundary.
- Keep the rule disabled. Stop if its existing cloud state is enabled, missing, ambiguous or managed by another deployment system.
- Reject resource templates, other resource types, arbitrary query input and enabled rules.
- Do not bypass environment protections. Under the latest explicit end-to-end setup authorization, configuration changes may be reviewed and merged through the protected PR path after required CI passes; never force-push or bypass required checks.
- Live KQL validation is manual, opt-in, aggregate-only, with no raw log/identity output.
- Never commit credentials, subscription/tenant identifiers or sensitive telemetry.
- Reproducible bootstrap scripts must default to preview, pin the existing subscription, reuse discovered resources and surface Azure error codes without publishing identifiers or tokens. The latest explicit setup authorization supersedes the earlier operator-only bootstrap restriction.

## Validation and documentation

Read `docs/PROJECT_STATUS.md` first on subsequent sessions. Phase 2 synthetic ingestion is offline only: local code and REST resource bodies are permitted, but DCR/table provisioning, live ingestion, new roles and rule activation still require explicit approval. Do not infer approval from a cost estimate or create a live sender workflow until its scope is authorized.

Phase 3 permits the manual main-only `check-health.yml` read-only OIDC workflow using existing workspace metadata and analytics-rule inventory permissions. It must not execute log queries, read the subscription export without authorization, change resources/roles, enable SentinelHealth or introduce a schedule. Unknown telemetry/runtime/export evidence must remain explicit. Local fault injection must not affect Azure collection.

Phase 4 risk correlation is synthetic and offline only. Findings are local investigation artifacts, not Sentinel incidents. Keep canonical identity joins explicit, preserve source-event lineage, reject conflicting duplicates and keep health uncertainty separate from risk. Baseline exceptions do not authorize Azure operations. No new cloud workflow, connector, role, rule activation or automated containment is authorized by this phase.

Run `python -m unittest discover -s tests -v` and `python -m scripts.validate_detection`.
Document purpose, data sources, KQL, MITRE mapping, entities, false positives,
testing, actual deployment evidence and limitations. Offline simulation is not Kusto execution.
A task is complete only when its authorized checks are complete; report external blockers honestly.
