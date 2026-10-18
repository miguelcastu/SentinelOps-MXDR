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
- Never use the personal Azure user/Owner session for autonomous cloud operations.
- Never create Azure identities, assign roles or grant additional RBAC permissions autonomously.
- Missing OIDC/RBAC prerequisites block that cloud operation; document the exact manual prerequisite.
- Never delete Azure resources or deploy unrelated infrastructure.

## Deployment boundary

- Only update the existing AZ-DET-001 rule at the configured UUID. Never discover a new target by guesswork.
- Keep the rule disabled. Stop if its existing cloud state is enabled, missing, ambiguous or managed by another deployment system.
- Reject resource templates, other resource types, arbitrary query input and enabled rules.
- Do not bypass environment protections or merge a PR on the operator's behalf.
- Live KQL validation is manual, opt-in, aggregate-only, with no raw log/identity output.
- Never commit credentials, subscription/tenant identifiers or sensitive telemetry.

## Validation and documentation

Run `python -m unittest discover -s tests -v` and `python -m scripts.validate_detection`.
Document purpose, data sources, KQL, MITRE mapping, entities, false positives,
testing, actual deployment evidence and limitations. Offline simulation is not Kusto execution.
A task is complete only when its authorized checks are complete; report external blockers honestly.
