# Phase 4 validation: synthetic risk correlation

This phase implements an offline Python risk engine and a reproducible Atlas Financial investigation scenario. It introduces no Azure resource, ingestion, query, identity/role change, paid feature, workflow schedule or incident.

## Reproduce

```powershell
python -m rba
python -m unittest discover -s tests -v
python -m scripts.validate_detection
```

Default output under `.local/rba/`: original synthetic dataset, full JSON risk report, investigation Markdown and an interactive standalone entity/timeline report. Evidence is explicitly synthetic; it is not Kusto execution or a Sentinel alert/incident.

## Observed synthetic outcomes

The default dataset contains 18 envelopes, 16 unique source events, two deduplicated replays and three accounts. Exactly one account, `synthetic-user-00`, qualifies at **12:13 UTC** on 18 October 2026 after the ordered sequence completes. First/peak risk: **75.7182**; risk as of 12:20 UTC: **64.4110**. Priority is High and confidence is Low because endpoint collection health is Unknown.

The maintenance account peaks at **33.7962** and the administrative-noise account at **14.1382**, with neither producing a finding. The nine scenario checks match their expected outcomes. These are fixture measurements, not real-world detection accuracy or cloud evidence.

Canonical unique-event SHA-256:

`24788dcaae44b0184badec1e533afa4f5116131b2e07bca1b0986c45d40108ad`

The same original-event dataset and policy produce stable scores/IDs regardless of input order or repeated transport envelopes. The report retains its historical finding after current risk expires within the bounded lookback.

## Verification scope

Tests exercise weak-signal correlation, benign/edge controls, strict stage timing and ties, host/scope/account isolation, same-IP users, original-ID conflicts, distinct same-time occurrences, saturation under 500 failures, exact half-life decay, window expiry, proportional contribution/global caps, baseline scope/time/actor constraints, missing/stale health, confidence separation, synthetic-only/privacy guards, input/actor bounds, adapter compatibility and standalone-report escaping. CLI tests deny socket/subprocess access while running the complete demonstration.

Final local suite: **112 tests pass on Python 3.12 and Python 3.15**. Independent Draft 2020-12 JSON Schema validates all 95 signal cases across the default dataset and scenario fixtures; six workflow YAML files parse, actionlint and documentation links pass. Importing the actual historical Phase 3 report correctly leaves source health Unknown and preserves the synthetic finding. No third-party runtime dependency is required. Protected remote CI evidence is tracked in the project checkpoint.

[Synthetic dataset](../../evidence/phase-4/dataset.synthetic.json) and [risk report](../../evidence/phase-4/risk-report.synthetic.json) are committed as reproducible evidence. The report includes the contribution ledger, original-event chain, configuration hash, source-health limitations and nine expected scenario outcomes. It is never labeled Azure validation.

Existing Azure rule definitions and deployment scripts were not changed. The previous [Phase 3 OIDC audit](https://github.com/miguelcastu/SentinelOps-MXDR/actions/runs/39153342114) remains historical; this phase does not claim a new Azure audit or refreshed credit balance. No deployment or health workflow needs to run to demonstrate this offline capability.

Read the [engineering design/runbook](../operations/risk-correlation.md) for scoring choices, current MITRE references, baselines and known coverage gaps. [PROJECT_STATUS.md](../PROJECT_STATUS.md) records delivery and the next phase.

Delivery: [PR #9](https://github.com/miguelcastu/SentinelOps-MXDR/pull/9), implementation `d46f19b`. The [required implementation CI](https://github.com/miguelcastu/SentinelOps-MXDR/actions/runs/39167931811) passed; the PR records final-head checks and the protected merge. No Azure deployment or health workflow was invoked.
