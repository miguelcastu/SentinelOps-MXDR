# Platform setup evidence ? 18 October 2026

Baseline: existing id-sentinelops-ci, one disabled Scheduled AZ-DET-001, one existing enabled Fusion rule, no Sentinel repository synchronization, no ARM connector resources and one subscription diagnostic export. No duplicate identity/rule was provisioned in setup.

Workspace: West Europe, per-GB pricing, **30-day retention**, **0.1 GB daily cap**. Subscription/billing spending limit On; currency EUR, billing type Free, status Active. These settings were read, not changed.

Credit API: one sign-up lot, **200 USD / 175.994368 EUR**, active from 13 October through **12 November 2026, 18:00:16 UTC** (19:00:16 Europe/Madrid). Closed balance equals original credit; available credit events report zero charges. This is service-reported billing evidence, not a guarantee about unposted usage. The month-to-date Cost Management query returned HTTP 429; no polling/export job was created. Zero payments-on-account is not the promotional credit balance.

MFA: first required role-definition write returned HTTP 401 RequestDisallowedByAzure and an official challenge. Supported interactive MFA completed; ARM core token contains mfa/p1; Azure accepted the metadata-role PUT with HTTP 201. No security policy was weakened; Cloud Shell/browser-token extraction was not used.

Setup completed against the existing identity: two narrow roles/assignments, one exact federated credential, encrypted GitHub identifiers and original rule UUID. No Log Analytics query role was granted during bootstrap.

First OIDC attempt failed with AADSTS700213 due to legacy subject format. The actual token and GitHub API report immutable subject format; the existing federation was corrected without duplication. The second attempt authenticated successfully but failed on an Azure rule operation. This remains failure evidence, not a deployment success. Final deployment/idempotency/drift/preservation results are recorded when verified.
