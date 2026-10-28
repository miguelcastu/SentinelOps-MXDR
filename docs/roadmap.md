# Roadmap and acceptance criteria

The eight-phase mission is tracked in [PROJECT_STATUS.md](PROJECT_STATUS.md), the authoritative resume checkpoint.

| Phase | Implemented | Remaining gate |
|---|---|---|
| 1. Detection engineering | Two disabled rules, scoped OIDC CI/CD, fresh drift audit and synthetic triage | Actual alert -> incident -> investigation -> classification; activation/query/test approval required |
| 2. Advanced ingestion | Synthetic source, normalization, schema, bounded client, DCR/table REST bodies, tests and runbook | Explicit resource/cost/RBAC approval before provision/upload and destination verification |
| 3. Platform health | Evaluator, eleven safe faults, local dashboard, KQL library and actual read-only OIDC configuration audit verified | Acceptance met for simulations/configuration; live query/export/runtime health remains permission-limited |
| 4. Risk-based detection | Offline entity scoring, strict multi-stage rule, deduplication/decay/caps, maintenance controls, replay and 112 passing tests | Acceptance met with labeled synthetic correlation; no live incident claim |
| 5. SOAR | Planned | Offline orchestration/audit; paid services require approval |
| 6. IaC and advanced CI/CD | Existing restricted rule CI/CD | Platform Bicep, preview, recovery and authorized deployment |
| 7. Customer operations | Initial onboarding | Fictional customer package and service tickets |
| 8. Portfolio completion | Existing technical README/evidence | Final acceptance, demo and verified release |

Earlier AzureActivity ingestion and disabled-rule deployment evidence remain valid. Offline ingestion does not complete Phase 1 or establish a second cloud source. Every increment must preserve the subscription, protections and spending controls.

The 28 October [personal Linux machine increment](onboarding/local-linux-ama.md)
adds local VM preparation and a fixed Arc/AMA Syslog design to Phase 2. This
does not replace the separate synthetic-authentication design or establish live
AMA ingestion. The [local/cloud acceptance stages](validation/local-linux-ama.md)
and scoped resource/ingestion approval must be satisfied before treating the
machine as an active source or developing detections that depend on its logs.
