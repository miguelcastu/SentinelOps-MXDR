# Phase 1 audit and Phase 2 offline ingestion evidence

Date: 18 October 2026. Customer scenario: **Atlas Financial (fictional)**. No affiliation with any security provider is implied.

## Actual read-only Azure and GitHub baseline

The operator's existing MFA-authenticated session was used only for administrative verification, not deployments. It matched the private subscription/tenant pin. Raw responses remain ignored under `.local/phase-1-2-baseline.private.json`.

- Existing workspace: West Europe, retention 30 days, daily cap 0.1 GB.
- Resource group inventory: one Log Analytics workspace, one OperationsManagement solution and the existing managed identity. No DCR, DCE, VM or new service.
- One subscription diagnostic export remains configured. This is configuration evidence; fresh query/telemetry health was not measured in this run.
- Both scheduled rules: exactly one matching display name, disabled, every managed property equals the repository JSON. Existing Fusion was left untouched.
- Main remains protected with administrators enforced and required `offline` checks.
- Last actual cloud deployments remain successful: [AZ-DET-001](https://github.com/miguelcastu/SentinelOps-MXDR/actions/runs/39134917660), [AZ-DET-002](https://github.com/miguelcastu/SentinelOps-MXDR/actions/runs/39134917548). No redundant deployment was triggered to generate activity.

## Credit and pricing verification

Microsoft Billing reports subscription billing type **Free**, subscription status **Active**, billing profile spending limit **On**. The credit lots API reports **200 USD / 175.99436818021823 EUR** closed balance, `isEstimatedBalance=false`, expiring **12 November 2026 at 18:00:16 UTC**. This is the API's published balance; it is not a guarantee against delayed usage charges. No billing plan, spending limit, cap, retention, budget, role or logging change was made.

The Microsoft [retail prices API](https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices) was queried read-only for current West Europe EUR Consumption prices. The Sentinel Pay-as-you-go Analysis meter returned **EUR 4.919 per GB**; the Log Analytics Analytics Logs Data Ingestion billable tier returned **EUR 2.6311 per GB**. Their conservative sum is EUR 7.5501/GB; do not double-count them if the actual workspace uses simplified combined pricing. A current per-subscription effective rate and pricing model must be verified before deployment; promotional/trial rates were not assumed to make ingestion free.

Conservative planning example: round the combined ingestion/analysis allowance upward to **EUR 10/GB**, and count every serialized normalized byte including JSON overhead and up to three accepted copies from retries. Default 24-event payload: **14,833 bytes**; volume allowance **44,499 bytes**, estimated **EUR 0.000445**. Whole-run local byte ceiling: 65,536 x 3 -> 196,608 bytes, estimate **EUR 0.001967**. A proposed approval allowance of **EUR 0.01 total for one run** leaves margin. This is neither a guaranteed price nor a new Azure spending cap; if effective rates or required services invalidate it, stop and seek a revised approval. No schedule means no recurring daily sender workload; on the single test day, daily and total ingestion estimates are equal. Existing platform costs continue independently.

No custom table/DCR was created, no synthetic rows were uploaded and no log query was executed. The work introduced **zero Azure workload/resource changes**, so no ingestion estimate above has been consumed by this implementation. Network reads of configuration and public pricing are distinct from ingestion.

## Reproducible offline results

```powershell
python -m ingestion
python -m scripts.assess_detections
python -m scripts.validate_detection
python -m unittest discover -s tests -v
```

Default demo: 24 source events, 8 failures / 16 successes, 24 stable unique IDs, one UTF-8 JSON batch, 14,833 bytes, worst case three HTTP attempts, **zero Azure requests**. Normalized payload SHA-256:

`a5e5950e8c8ebacc08aa7d27d230b167c771b4655b2f4edf7ddb796ee91e2828`

Tests cover UTC conversion and year boundary, deterministic IDs, source schema evolution, wrong field types, documentation IP ranges, unknown fields, duplicates, mixed batches, maximum event/byte/request limits, exact DCR/table column consistency, wrong target rejection, explicit approval, TLS/redirect/timeout behavior, throttling, Retry-After dates and stop conditions, finite retries, redacted transport failures and aggregate-only receipts. HTTP tests use mocks and prove client behavior, not Azure ingestion.

Final local suite: **67 tests pass on Python 3.12 and Python 3.15**. Both existing rule validators pass; 100 generated events independently pass Draft 2020-12 JSON Schema with date-time format checking. Five workflow YAML files parse, actionlint passes, and local Markdown links resolve. Staged whitespace and private-target/credential scans are part of the delivery checks. Standard-library-only CI requires no new package installation.

The triage assessment reports `real_false_positive_rate=null` and `kusto_executed=false`; each rule has one synthetic benign match and a failed-operation coverage gap. Neither rule was tuned based on an invented real-data baseline.

## Remaining external acceptance

Phase 1: [controlled incident test](../detections/lifecycle-validation.md) needs explicit activation/test-event/query/incident permissions. No alert, Defender incident or classification evidence exists yet.

Phase 2: [source onboarding runbook](../onboarding/synthetic-authentication.md) is complete for offline engineering. Live acceptance needs approval of table/DCR creation, separate narrow provisioner/sender/query roles, reviewed OIDC workflows and one bounded upload/query. Both source formats are demonstrable locally/with historical AzureActivity evidence; only AzureActivity has prior actual cloud ingestion evidence. A second operational cloud connector is **not** claimed.

CI/PR references and current acceptance status are maintained in [PROJECT_STATUS.md](../PROJECT_STATUS.md).
