# Troubleshooting detection CI/CD

| Symptom | Check / resolution |
|---|---|
| Missing environment configuration | Populate the named environment secret/variable using the deployment runbook. No personal-session fallback. |
| OIDC federation failure | Check client/tenant IDs, issuer, audience, exact environment subject and main-only branch policy privately. Do not create a password. |
| Azure 403 / request failed | Administrator reviews exact rule/workspace scope and inherited RBAC. Do not grant Contributor or retry with Owner. |
| Azure 404 / request failed | Confirm existing workspace and original rule UUID. No replacement resource is created. |
| No unique matching rule | Stop; reconcile names and IDs privately with the operator before configuring the target. |
| Existing rule enabled | Stop for an explicit operator decision. The pipeline will not disable a live rule automatically. |
| Etag/concurrency conflict | Review who changed the existing resource. No automatic etag refresh/retry or unconditional PUT. |
| Persisted property mismatch | Deployment is not verified. Inspect the exact source/API behavior privately; do not enable the rule or report success. |
| Query/schema validation failure | Review the source and API contract; changing just the validator to permit an unreviewed body defeats the gate. |
| Live query returns zero | May be ordinary lab inactivity. Check time window and source onboarding without generating paid activity or duplicating exports. |
| Query aggregate rejected | Partial errors, unexpected columns and raw rows are intentionally rejected. Never print the full response into public CI. |
| Workflow skipped after visibility change | Jobs require a public repository for free standard runners. Reassess cost before modifying the guard. |
| Git push rejected for workflow permission | Use an authorized GitHub credential with workflow-write permission. Keep the validated local commit; do not weaken validation or expose credentials. |

Diagnostics may contain tenant/subscription IDs or identities. Use private Azure/GitHub views and publish only sanitized outcomes. Do not change subscription, pricing, retention, caps, data connectors or RBAC to make a failed job green.

Recovery is a reviewed Git revert and PR through the same pipeline, using an earlier **disabled** approved definition. Do not restore an enabled rule, delete resources or automatically run an out-of-band deployment.
