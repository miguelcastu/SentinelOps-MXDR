# Five-minute engineering demonstration

Audience: a hiring manager and an engineer. Goal: demonstrate a coherent,
reproducible engineering system and show where its evidence stops. No Azure
authentication, deployment, VM boot or live ingestion is needed for this tour.
Atlas Financial and the generated attack/case are fictional.

## Prepare before the meeting

Use Python 3.12+ in a clean checkout. Run the required checks once, confirm
their result and keep the output available; do not spend the presentation
watching a test runner. Keep private `.local/` identity/credential files closed.

```powershell
python -m unittest discover -s tests -v
python -m scripts.validate_detection
python customer/atlas-financial/validate.py
python -m ingestion
python -m portfolio
python -m platform_health
python -m rba
python -m soar
python -m lab
```

The CLIs write local artifacts and label their evidence. Open the generated
health/RBA HTML artifacts locally; do not publish private working directories.
`python -m lab` builds the integrated offline dashboard at
`.local/lab/index.html`. Open it locally and keep the case/audit artifacts
available for the walkthrough. Verify the commands from a fresh output
directory before the meeting rather than relying on a prior generated report.

## Timed narrative

| Time | Show | Say / demonstrate |
|---|---|---|
| 00:00-00:35 | [Architecture](../architecture/overview.md) | “This lab separates data collection, configuration control and investigation. AzureActivity uses an existing export. One owned Linux guest used Arc/AMA. GitHub controls fixed configuration through OIDC.” |
| 00:35-01:15 | [Coverage matrix](../../customer/atlas-financial/detection-coverage.md), AZ-DET-012 KQL | “Twelve deployed definitions are disabled. The correlation preserves original event IDs, requires ordered actions and matches canonical scope. A role grant plus a diagnostic write is an investigation hypothesis, not automatic proof of compromise.” |
| 01:15-02:05 | Local RBA replay | Show the ordered authentication -> role -> diagnostic -> endpoint chain. Inspect contribution/decay, a benign maintenance lookalike and the Unknown endpoint-health confidence limit. State “synthetic” aloud. |
| 02:05-02:55 | Local case-workflow result and audit | Follow the correlated finding through intake, evidence/context, a recorded human decision and case classification. Show replay/idempotency and one failure/recovery result. A local case is not a Sentinel incident. |
| 02:55-03:35 | Local health fault dashboard | Select missing/delayed/schema/drift cases. Explain why Unknown query access differs from zero events, and why a powered-off guest is not required to emit a heartbeat. |
| 03:35-04:15 | [OIDC workflow](../../.github/workflows/deploy-portfolio.yml), [security boundary](../security.md) | Show fixed approval fingerprint, exact-resource permissions, main-only environment and actual REST read-back. PR validation has no Azure deployment permission. |
| 04:15-04:45 | [Actual AMA aggregate](../../evidence/local-linux-ama/ingestion.sanitized.json), [shutdown](../../evidence/local-linux-ama/shutdown.sanitized.json) | “This dated actual run delivered ten total/unique messages, 2,600 billable bytes. The VM was shut down. This proves that one transport test; it does not promise native SSH coverage or a zero invoice.” |
| 04:45-05:00 | [Customer package](../../customer/atlas-financial/README.md), [current acceptance](../PROJECT_STATUS.md) | Close on operational ownership, risk register, recovery and exact evidence limits. Identify any still-unexecuted live requirement directly. |

## Three useful live interactions

1. Select the benign-maintenance RBA scenario and explain the narrowly scoped
   exception. It does not exempt all actions by the same actor.
2. Show a duplicated original event and explain why the source lineage stays
   one event, while conflicting data for the same original ID is rejected.
3. Open the case audit record and point to the human decision/evidence needed
   before the workflow can reach its final state.

If a command fails, keep the error and describe its boundary. Do not switch
to Azure or make a chargeable request to rescue the presentation. The checked-in
sanitized evidence and reproducible fixtures provide a subscription-independent
fallback. Do not claim an actual live alert lifecycle unless current project
status links the real rule, alert, incident, investigation and classification.
