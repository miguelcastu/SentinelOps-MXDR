# Detection CI/CD validation record

Assessment date: 18 October 2026 (Europe/Madrid).

## Observed starting state

- Repository `miguelcastu/SentinelOps-MXDR` is public; authenticated GitHub access has push/admin permission.
- Initial `main` commit: `681ca1b41f11340e04d26f1068c5e4844dff900a`.
- The original two offline repository tests passed.
- Azure CLI 2.91.0 is installed. Its local account metadata identifies the existing subscription and a personal user session. No Azure cloud API was called with that session.
- GitHub initially returned an empty environment list. `sentinel-lab` secrets, variables and deployment branch policies did not exist. Main protection was not returned (HTTP 404).
- The managed identity, Azure RBAC assignments, federated credential and existing AZ-DET-001 UUID/state remain **unverified**. Do not infer they are absent from missing GitHub configuration.
- No subscription selection/plan, Azure resource, ingestion, retention, budget or cap was changed. No live log query was run.

## Implementation checks

GitHub setup completed without Azure access: the `sentinel-lab` environment permits only branch `main`; deployment, exclusive-owner and live-query review flags are all `false`. No credentials or target rule UUID were invented or populated. Main protection requires a PR, the `offline` status check, current-branch validation and resolved conversations; administrator enforcement is on and force pushes/deletion are prohibited. The formal reviewer count is zero so the sole maintainer can review and merge their own PR; this does not bypass the required PR or CI.

Run locally:

```powershell
python -m scripts.validate_detection
python -m unittest discover -s tests -v
```

The suite includes synthetic filter cases, unsafe JSON/KQL mutations, identity/subscription/ref guards, missing-rule/no-write behavior, concurrency failure, persisted-state drift and aggregate privacy checks. Azure responses in unit tests are mocks; they are not cloud evidence. A separate standards JSON Schema and YAML validation was also performed using ephemeral development tools, with no project runtime dependency added.

Local results: **28 tests passed**, including 21 synthetic event fixtures, on Python 3.12.14 and 3.15.0. Draft 2020-12 JSON Schema validation and all three YAML parses passed. `actionlint` v1.7.12 passed for all workflows; the downloaded upstream release was checksum-verified. `git diff --check` passed. Missing-prerequisite validation was exercised and stopped before any OIDC login or Azure request.

## Cloud acceptance — pending

Do not mark these complete without corresponding evidence:

| Gate | Evidence required |
|---|---|
| Restricted Azure prerequisite review | Operator confirms same subscription, least-privilege identity, exact existing disabled rule and exclusive ownership |
| Approved PR merged | Actual merged PR and commit |
| OIDC deployment succeeds | Successful deployment workflow run |
| Actual rule verified | Same workflow's final GET confirms the original ID and all approved disabled properties |
| Actual Kusto syntax and semantics | Optional read-only workflow's synthetic Mismatches=0 |
| Real data aggregate | Optional workflow's count-only output; zero is acceptable and limited evidence |

The approximately 175 EUR credit balance and expiry have not been verified. This work did not initiate chargeable Azure activity. It does not establish that already-running resources have stopped accruing charges.
