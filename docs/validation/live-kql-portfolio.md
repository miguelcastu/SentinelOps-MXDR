# Bounded live KQL portfolio verification

The fixed [validator](../../scripts/validate_portfolio_live.py) provides a
separate runtime check for all twelve AzureActivity definitions. Its default
mode is an **offline preview**. This document records the implementation and
test contract; it does not claim Azure execution before a separately recorded
successful run and sanitized evidence.

```powershell
python -m scripts.validate_portfolio_live
python -m unittest discover -s tests -p test_portfolio_live.py -v
```

## Exact scope and approval

`fixed_query()` validates AZ-DET-001/002 through their existing validators and
AZ-DET-003..012 through the complete fixed portfolio validator. Each original
KQL body is wrapped in its own zero-argument local function; the sequence
rule's internal `let` statements remain intact. A strict union reduces each
function to `DetectionId` and `Matches=count()` and projects only those two
columns. Every source already limits AzureActivity to one hour; the request
also supplies `timespan: PT1H`. No arbitrary table, query, rule, workspace or
time-window option exists.

An operator-approved execution runs from clean reviewed merged main, outside
GitHub Actions, through the existing pinned personal MFA session. Routine
deployment still uses OIDC; this is aggregate-only verification, not a personal
deployment path. A private record at
`.local/completion/live-kql-approved.private.json` must contain the current
preview's `query_sha256` as `sha256` and `allow_one_aggregate_query: true`.
The local subscription/tenant pin is read and validated before authentication.
The account must match exactly; no account selection, billing upgrade or
permission fallback is attempted.

`--apply` performs one existing-workspace metadata GET to independently verify
the workspace ID/West Europe region and obtain its customer ID. It requests
the documented Logs token audience `https://api.loganalytics.io`, then issues
**one** POST to the fixed HTTPS Logs endpoint. It adds no CI query role, source,
ingestion, rule activation, incident, schedule or resource mutation.

## Single-attempt and output boundaries

Before POST, exclusive creation claims
`.local/completion/live-kql-attempt.private.json`. A process interruption,
timeout, partial result or ambiguous response leaves that ledger consumed.
There is no retry loop. Do not delete/reset the ledger or replay a query to
make evidence appear successful. If an actual failure needs a fresh test, first
review its cause and obtain a separately scoped attempt rather than treating
this record as permission for repeated queries.

The HTTP client refuses redirects, uses a sixty-second timeout and reads no
more than one MiB plus a size-check byte. Error output contains bounded error
codes only, never Azure message bodies, KQL, identities, tokens or resource IDs.
The result must be exactly one PrimaryResult table, exact typed columns, twelve
unique fixed IDs and nonnegative integer counts. Extra/raw columns, missing or
duplicate rows, a partial error, oversized body and non-JSON response fail
closed. Zero matches is a valid quiet one-hour observation.

A successful run writes `.local/completion/live-kql.sanitized.json` with actual
Kusto execution, query fingerprint, timestamp, twelve match counts and explicit
limitations. It includes no raw telemetry or workspace/customer/subscription
identifiers. Public evidence must be reviewed before publication. A completed
ledger blocks repeating even a successful run.

## What this establishes

A successful actual run establishes that all twelve fixed KQL definitions
compile and execute together against the existing AzureActivity schema within
that bounded window. It does **not** establish a measured false-positive rate,
calibrated precision/recall, complete source arrival, incident creation or
scheduled rule execution. Counts can include legitimate administrative activity.
Disabled deployment state is unchanged. The separate real alert/incident
lifecycle and fictional SOAR case remain different acceptance evidence.

The implementation is tested offline with fake HTTP responses and real fixed
query generation. Tests verify zero-auth preview, complete nested-let wrapping,
approval/pin/clean-main gates, exact response typing, one-request budgets,
metadata mismatch, consumed ambiguous attempts, response bounds, redirect
refusal and safe error codes. These tests are not Kusto execution. Final actual
execution, if performed, must be linked from the project's completion evidence
after its sanitized result is obtained.
