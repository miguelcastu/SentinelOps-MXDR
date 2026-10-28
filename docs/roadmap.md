# Roadmap and acceptance criteria

The eight-phase mission is tracked in [PROJECT_STATUS.md](PROJECT_STATUS.md), the authoritative resume checkpoint.

| Phase | Implemented | Remaining gate |
|---|---|---|
| 1. Detection engineering | Twelve disabled rules, scoped OIDC CI/CD, drift audit and synthetic triage | Actual alert -> incident -> investigation -> classification; activation/query/test approval required |
| 2. Advanced ingestion | Synthetic offline pipeline plus actual one-machine Arc/AMA Syslog pilot, ten messages reconciled, guest stopped | Separate synthetic-auth custom-table provisioning/upload remains unapproved; AMA continuous health and broader collection not implemented |
| 3. Platform health | Evaluator, eleven safe faults, local dashboard, KQL library and actual read-only OIDC configuration audit verified | Acceptance met for simulations/configuration; live query/export/runtime health remains permission-limited |
| 4. Risk-based detection | Offline entity scoring, strict multi-stage rule, deduplication/decay/caps, maintenance controls, replay and 112 passing tests | Acceptance met with labeled synthetic correlation; no live incident claim |
| 5. SOAR | Planned | Offline orchestration/audit; paid services require approval |
| 6. IaC and advanced CI/CD | Existing restricted rule CI/CD | Platform Bicep, preview, recovery and authorized deployment |
| 7. Customer operations | Initial onboarding | Fictional customer package and service tickets |
| 8. Portfolio completion | Existing technical README/evidence | Final acceptance, demo and verified release |

Earlier AzureActivity ingestion and disabled-rule deployment evidence remain valid. Offline synthetic authentication does not complete Phase 1; the separate Linux pilot establishes only its bounded Syslog acceptance. Every increment must preserve the subscription, protections and spending controls.

The 28 October [personal Linux machine increment](onboarding/local-linux-ama.md)
completed local VM preparation, Arc registration, fixed AMA/DCR/association,
exact RBAC, main OIDC verification and one reconciled ten-message Syslog batch.
The guest is stopped. [Actual evidence](validation/local-linux-ama.md) records
2,600 billable bytes and distinguishes this transport proof from ongoing
monitoring, native SSH logs, active alerts and monetary cost measurement.
Another batch, source expansion or activation requires separate authorization;
offline Linux detection/health policy design can be prepared first.
