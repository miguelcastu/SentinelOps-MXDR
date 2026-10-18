# Second-detection test evidence

Date: 18 October 2026 (Europe/Madrid).

- PR #1 was confirmed merged; the second implementation starts from main commit `f024e76618bda428d7ef737c5d7b35d0f062443c`.
- Before this test, `sentinel-lab` had no Azure environment secrets; the three earlier approval flags remained false. Azure managed identities/RBAC were not inspected using the personal session.
- AZ-DET-002 is implemented as a disabled Scheduled rule with a fixed reviewed UUID, duplicate checks and final persisted-property verification.
- Local tests: **41 passed**, including the original suite plus 17 second-rule event fixtures and mocked creation, duplicate/conflict, disabled-state, inventory-error, verification-drift and operator-bootstrap guards.
- Both constrained JSON Schemas passed independent standards validation. Four workflows passed YAML parsing and actionlint. Documentation relative links passed.
- GitHub environment public-key retrieval succeeded. PyNaCl 1.6.2 sealed-box encryption was tested with synthetic values, not user identifiers.
- The bootstrap preview succeeded against cached local account metadata and a private ignored subscription pin. The agent did not run administrative `--apply`.

Pending evidence: operator-run OIDC setup, second PR review/merge, successful **Deploy Additional Disabled Detection** workflow and its actual Azure GET confirmation. Offline mocks, bootstrap completion and GitHub CI do not independently prove Sentinel deployment or real-data false-positive performance.

No connector, billable compute, subscription selection/plan, ingestion, retention, cap or budget was changed by the agent. No live query or chargeable experiment was initiated. Existing Azure resources can continue accruing their own charges; the reported credit balance remains unverified.
