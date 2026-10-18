# Verified second disabled detection

AZ-DET-002 observes successful Azure RBAC role assignment writes in existing AzureActivity data. It was created through the protected-main OIDC workflow and its final Azure GET matches the disabled source definition. See [actual deployment evidence](../validation/platform-setup.md).

The existing **id-sentinelops-ci** is reused. Azure accepted an RBAC write assignment on the fixed AZ-DET-002 resource UUID before the rule existed. No workspace-wide write grant or additional identity was needed. A separate read-only analytics inventory role at the existing workspace supports duplicate detection checks. Query and infrastructure permissions were not granted.

Reproducible authorized setup (preview without --apply):

```powershell
uv run --python 3.12 --with pynacl==1.6.2 --no-project python -m scripts.bootstrap_oidc --apply --include-additional
```

This prepares exact-resource RBAC, identity federation and environment approval; it does not create or enable a rule itself. The CI workflow creates/updates only the fixed reviewed UUID and rejects duplicate, conflicting, enabled or incompletely inventoried targets. GET then compares every managed property. Unrequested deployment skips cloud operations explicitly; requested deployment with missing access fails.

The 17 synthetic cases include legitimate administration that also matches. Real historical false-positive measurement and activation remain separately reviewed work. No connector, paid compute, ingestion, retention, cap or billing change is required.
