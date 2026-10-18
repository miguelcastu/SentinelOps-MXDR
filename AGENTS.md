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
- The operator reports approximately 175 EUR of promotional credit; balance and expiry are unverified.
- Prefer offline work and free public-repository standard GitHub runners. Do not consume credit for experiments.
- Never create VMs, databases, workspaces, connectors, Logic Apps, paid resources or Defender plans.
- Never change pricing, retention, ingestion, daily caps, budgets or diagnostic settings.
- The operator explicitly authorized administrative setup on 18 October 2026: reuse `id-sentinelops-ci`, configure narrow custom RBAC and exact GitHub OIDC trust, and populate GitHub environment identifiers. The personal session may be used for that setup and verification only, with valid MFA.
- Routine rule deployments must use GitHub OIDC, never the personal account. Do not create duplicate identities, grant broad roles, weaken MFA/Conditional Access or use Cloud Shell.
- Request human intervention only for unavoidable MFA/consent or sensitive changes outside the authorized scope. Continue independent work while authentication is pending.
- Never delete Azure resources or deploy unrelated infrastructure.

## Deployment boundary

- Update AZ-DET-001 only at its configured existing UUID.
- The operator authorized one additional disabled detection, AZ-DET-002 (Azure Role Assignment Created), on 18 October 2026. Its dedicated workflow may create/update only its fixed, reviewed UUID. No other resource creation is authorized.
- Keep the rule disabled. Stop if its existing cloud state is enabled, missing, ambiguous or managed by another deployment system.
- Reject resource templates, other resource types, arbitrary query input and enabled rules.
- Do not bypass environment protections. Under the latest explicit end-to-end setup authorization, configuration changes may be reviewed and merged through the protected PR path after required CI passes; never force-push or bypass required checks.
- Live KQL validation is manual, opt-in, aggregate-only, with no raw log/identity output.
- Never commit credentials, subscription/tenant identifiers or sensitive telemetry.
- Reproducible bootstrap scripts must default to preview, pin the existing subscription, reuse discovered resources and surface Azure error codes without publishing identifiers or tokens. The latest explicit setup authorization supersedes the earlier operator-only bootstrap restriction.

## Validation and documentation

Run `python -m unittest discover -s tests -v` and `python -m scripts.validate_detection`.
Document purpose, data sources, KQL, MITRE mapping, entities, false positives,
testing, actual deployment evidence and limitations. Offline simulation is not Kusto execution.
A task is complete only when its authorized checks are complete; report external blockers honestly.
