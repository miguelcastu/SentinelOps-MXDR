# Platform setup evidence - 18 October 2026

Baseline: existing id-sentinelops-ci, one disabled Scheduled AZ-DET-001, one existing enabled Fusion rule, no Sentinel repository synchronization, no ARM connector resources and one subscription diagnostic export. No duplicate identity/rule was provisioned in setup.

Workspace: West Europe, per-GB pricing, **30-day retention**, **0.1 GB daily cap**. Subscription/billing spending limit On; currency EUR, billing type Free, status Active. These settings were read, not changed.

Credit API: one sign-up lot, **200 USD / 175.994368 EUR**, active from 13 October through **12 November 2026, 18:00:16 UTC** (19:00:16 Europe/Madrid). Closed balance equals original credit; available credit events report zero charges. This is service-reported billing evidence, not a guarantee about unposted usage. The month-to-date Cost Management query returned HTTP 429; no polling/export job was created. Zero payments-on-account is not the promotional credit balance.

MFA: first required role-definition write returned HTTP 401 RequestDisallowedByAzure and an official challenge. Supported interactive MFA completed; ARM core token contains mfa/p1; Azure accepted the metadata-role PUT with HTTP 201. No security policy was weakened; Cloud Shell/browser-token extraction was not used.

Setup completed against the existing identity: two narrow roles/assignments, one exact federated credential, encrypted GitHub identifiers and original rule UUID. No Log Analytics query role was granted during bootstrap.

First OIDC attempt failed with AADSTS700213 due to legacy subject format. The actual token and GitHub API report immutable subject format; the existing federation was corrected without duplication. The second attempt authenticated successfully but failed on an Azure rule operation. This remains failure evidence, not a deployment success. Final deployment/idempotency/drift/preservation results are recorded when verified.

## Verified outcomes

| Check | Actual evidence |
|---|---|
| AZ-DET-001 deployment and final GET | [Successful OIDC run](https://github.com/miguelcastu/SentinelOps-MXDR/actions/runs/39133795266) |
| AZ-DET-002 creation and final GET | [Successful OIDC run](https://github.com/miguelcastu/SentinelOps-MXDR/actions/runs/39133985359) |
| Post-deployment drift | [Clean read-only comparison](https://github.com/miguelcastu/SentinelOps-MXDR/actions/runs/39133910235) |
| Pre-deployment drift detection | [Expected differences detected](https://github.com/miguelcastu/SentinelOps-MXDR/actions/runs/39133573227) |

An independent administrative GET confirmed each rule exactly matches all managed source properties, enabled=false, PT15M/PT1H. AZ-DET-001 retains its original resource ID. There are exactly three rules: the original Fusion rule and the two intended Scheduled detections, with no duplicate detection names.

The final private before/after comparison confirmed unchanged workspace configuration, subscription ID/policies, retention, daily cap, connector resources, repository sync configuration and both diagnostic-setting inventories. There is still exactly one managed identity.

RBAC audit confirmed three role definitions and four unique assignments: metadata read and analytics inventory read at the existing workspace, plus analytics read/write separately at each exact rule resource. Azure accepted the second exact-rule assignment before creation. No workspace-wide write, VM, pricing, ingestion, billing, role-management or delete action is granted to CI.

A full bootstrap rerun succeeded against the completed platform without creating duplicate identities, roles, assignments, federation or rules. Two preparation defects were fixed: resource discovery now uses the verified workspace REST endpoint, and existing roles are found by name because legacy Azure CLI create ignored the requested template Id. New role creation uses deterministic REST IDs. The original private backup is retained instead of overwritten on reruns.

Latest local validation: **50 tests**, two constrained JSON Schemas, five workflow YAML files, actionlint, documentation links and whitespace checks. Tests include synthetic benign/positive/negative/edge cases, immutable subjects, API-compatible parent techniques, legacy role reuse, drift and privacy safeguards. Live telemetry queries were not run; real false-positive rates and activated alert behavior remain unmeasured. Scheduled rules remain disabled.

Failures are preserved rather than reported as success: initial MFA denial; legacy OIDC subject mismatch; Sentinel rejection of subtechnique T1562.008 (the API requires parent T1562); and one bounded read timeout during a setup retry. The final verified deployments use the supported format and exact scopes.
