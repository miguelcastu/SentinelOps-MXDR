# Second disabled detection

AZ-DET-002 observes successful Azure RBAC role assignment writes in the existing AzureActivity data. Its fixed definition and 17 synthetic event cases are implemented. It remains disabled; SENTINEL_AZ_DET_002_APPROVED controls whether its workflow authenticates and writes.

The latest instructions authorize initial administration and require reuse of **id-sentinelops-ci**. The earlier proposal for id-sentinelops-rule002-ci is superseded; that identity was never created. Both workflows now reference the existing CI identity.

The [canonical runbook](detection-cicd.md) covers MFA, dependencies, OIDC and exact-rule RBAC. Bootstrap grants write access only to the existing AZ-DET-001 resource. It does not silently broaden access to create AZ-DET-002.

Creating a rule needs an applicable scope before the resource exists. Any additional assignment must be confined to the fixed rule where Azure supports it, or to analytics-rule operations in this existing workspace for initial creation, followed by reduction to the exact new resource. No Owner, Contributor, wildcard or infrastructure action is appropriate.

The approved workflow creates/updates only the reviewed UUID and refuses duplicate, conflicting, enabled or incompletely inventoried targets. It verifies the final GET against source. Missing approval skips cloud operations explicitly; requested deployment with missing credentials or insufficient access fails.

Synthetic tests do not establish Azure deployment or a real false-positive rate. No connector, paid compute, ingestion, retention, cap or billing change is needed.
