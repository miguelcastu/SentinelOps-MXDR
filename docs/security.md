# Deployment security boundary

Initial administration was explicitly authorized on 18 October 2026. The personal account is used only for MFA-protected setup and independent verification. Routine deployment uses the existing managed identity and short-lived GitHub OIDC, without client secrets or browser-token extraction.

Trust binds the immutable repository/owner identity to sentinel-lab, restricted to main. Protected PR validation controls changes. Actions are pinned to commit SHAs; PR validation has no OIDC permission or Azure environment.

RBAC limits approved analytics-rule operations and workspace metadata. Analytics-rule roles grant no pricing, ingestion configuration, retention, billing, role-management or deletion capability. The separate approved AMA roles below permit only their exact fixed collection resources. Permissions add together and must be reviewed at ancestor scopes. Payload validation supplements RBAC because alertRules/write cannot enforce enabled=false or distinguish create from update.

No job prints raw event rows, identities, tokens or Azure error bodies. Private snapshots/pins stay under ignored .local/. Public configuration exports remove identifiers/runtime identity metadata. Error codes and changed-property names remain visible for honest diagnostics.

There are no recurring health/drift jobs or sender workflows, paid add-on plans, new connector resources or billing changes. The separately approved AMA pilot added fixed collection resources and one bounded batch, described below. Optional live validation requires bounded access and cost review. Budgets are alerts; billing lag, existing consumption and promotional expiry still matter.

The [28 October actual RBAC audit](../evidence/local-linux-ama/preservation.sanitized.json)
verified **seven custom role definitions / eighteen unique assignments**:
twelve exact analytics-rule writers, two existing workspace read assignments,
one Arc-machine metadata reader and three exact DCR/extension/association
read/write assignments. Existing optional query scope was not expanded and
no new CI query permission was added. One reused managed identity and one
immutable-subject federation remain; no broad ancestor writer or role-management
permission was granted to CI. Permissions add together: all eighteen assignments
were checked, rather than assuming a narrow new role cancels older access.

Azure returned 404 when assigning at the absent DCR. The operator explicitly
approved [one-time personal initialization](deployment/ama-bootstrap-exception.md)
of only the same three fixed targets. Its completed ledger prevents reuse;
routine management remains main-only OIDC. The [successful OIDC
run](https://github.com/miguelcastu/SentinelOps-MXDR/actions/runs/40774219658)
verified already-matching resources without creating them. The local pilot
queried only aggregate counts/last-seen/billable bytes through the approved
personal session, not through expanded CI data access.

The public repository contains contracts and sanitized evidence, never client
secrets, the SSH private key, tenant/subscription IDs or raw logs. A fork/PR
cannot assume the existing main-only environment trust merely by copying the
code. Repository/environment administration and reviewed main changes remain
security-sensitive: exact RBAC and validation reduce their scope, but they do
not make a compromised authorized main workflow harmless. Do not weaken
branch protection, federation, MFA or environment gates. The Arc machine's
identity is separate from the CI identity; the guest is not joined to the
university directory. Its installed agent identity material stays private.
