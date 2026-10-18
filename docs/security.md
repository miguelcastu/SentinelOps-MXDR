# Deployment security boundary

Initial administration was explicitly authorized on 18 October 2026. The personal account is used only for MFA-protected setup and independent verification. Routine deployment uses the existing managed identity and short-lived GitHub OIDC, without client secrets or browser-token extraction.

Trust binds the immutable repository/owner identity to sentinel-lab, restricted to main. Protected PR validation controls changes. Actions are pinned to commit SHAs; PR validation has no OIDC permission or Azure environment.

RBAC limits approved analytics-rule operations and workspace metadata. It grants no infrastructure creation, pricing, ingestion, retention, billing, role-management or deletion capability. Permissions add together and must be reviewed at ancestor scopes. Payload validation supplements RBAC because alertRules/write cannot enforce enabled=false or distinguish create from update.

No job prints raw event rows, identities, tokens or Azure error bodies. Private snapshots/pins stay under ignored .local/. Public configuration exports remove identifiers/runtime identity metadata. Error codes and changed-property names remain visible for honest diagnostics.

There are no recurring health/drift jobs, paid services, new connectors, query audits or billing changes. Optional live validation requires bounded access and cost review. Budgets are alerts; billing lag, existing consumption and promotional expiry still matter.
