# Roadmap and acceptance criteria

The eight-phase mission is tracked in [PROJECT_STATUS.md](PROJECT_STATUS.md), the authoritative resume checkpoint.

| Phase | Implemented | Remaining gate |
|---|---|---|
| 1. Detection engineering | Two disabled rules, scoped OIDC CI/CD, fresh drift audit and synthetic triage | Actual alert -> incident -> investigation -> classification; activation/query/test approval required |
| 2. Advanced ingestion | Synthetic source, normalization, schema, bounded client, DCR/table REST bodies, tests and runbook | Explicit resource/cost/RBAC approval before provision/upload and destination verification |
| 3. Platform health | Source-specific expectations recorded | Health evaluator, safe fault injection and diagnostics |
| 4. Risk-based detection | Planned | Multi-signal scoring, deduplication and tests |
| 5. SOAR | Planned | Offline orchestration/audit; paid services require approval |
| 6. IaC and advanced CI/CD | Existing restricted rule CI/CD | Platform Bicep, preview, recovery and authorized deployment |
| 7. Customer operations | Initial onboarding | Fictional customer package and service tickets |
| 8. Portfolio completion | Existing technical README/evidence | Final acceptance, demo and verified release |

Earlier AzureActivity ingestion and disabled-rule deployment evidence remain valid. Offline ingestion does not complete Phase 1 or establish a second cloud source. Every increment must preserve the subscription, protections and spending controls.
