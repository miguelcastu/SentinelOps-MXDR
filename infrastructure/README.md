# Infrastructure configuration

The existing platform was initially provisioned manually. No platform Bicep deployment has been validated.

[ingestion/](ingestion/) contains proposed Direct DCR and custom-table **REST request bodies**, validated offline against the Python normalization contract. They have not been deployed. The destination placeholder is rendered only from the pinned existing workspace; no workspace pricing, retention or cap changes are included. See the [approval and onboarding runbook](../docs/onboarding/synthetic-authentication.md).

Phase 6 will model the supported existing platform and add a non-mutating preview, reviewed scoped OIDC workflows and recovery procedures. New resource deployment remains outside the approved detection-only boundary.
