# Final portfolio acceptance record

Review date: **3 November 2026**. This record freezes verified deliverables and
states the remaining live boundary. The original mission's real scheduled
alert/incident acceptance cannot be replaced by a local synthetic case.

## Reproduce the portfolio

Python 3.12+ is sufficient for all default demos and tests. No Azure account,
paid service or extra Python dependency is needed:

```powershell
python -m unittest discover -s tests -v
python -m scripts.validate_detection
python customer/atlas-financial/validate.py
python -m lab --bundle
```

Open `.local/lab/index.html` locally. It links source-health/risk explorers,
the detection catalog, original synthetic event lineage, SOAR case/audit and
separately labeled actual cloud records. The portable ZIP beside that output
contains allowlisted tracked source, workflows and generated public reports,
with a per-file SHA-256 manifest; keys, VM disks, private snapshots, SQLite and
raw screenshots are excluded. An unrelated file added beside output is never
implicitly included. ZIP creation is local, not a GitHub release publication.

The 24-event normalization fixture and the multi-source RBA fixture are
different exercises. The exact canonical RBA finding, seven original-event
IDs and original evidence chain are passed to SOAR; they are not reconstructed
from a screenshot or an unrelated sample.

## Acceptance by phase

| Phase | Verified deliverable | Evidence / remaining boundary |
|---|---|---|
| 1 | Twelve actual disabled definitions, sixty synthetic portfolio controls, investigations and isolated cloud-lifecycle implementation | Actual scheduled alert -> incident -> classified closure still requires the [concrete gated test](../deployment/synthetic-lifecycle.md); no live completion is asserted |
| 2 | Synthetic schema/normalizer/bounded transport plus two actual source proofs: AzureActivity and owned Linux AMA/Syslog | The latter reconciled ten unique messages; VM stopped. Optional synthetic custom table is not deployed or needed to claim those two source proofs |
| 3 | Three-source policy/inventory, sixteen local health scenarios, planned-stop/stale/partial-evidence handling, existing read-only OIDC config audit | Current live telemetry/runtime remain Unknown where not measured; historical pilot columns do not supply missing latency/schema metrics |
| 4 | Canonical identities, deduplication, sequence, decay/caps, maintenance context, nine replay scenarios and full evidence chain | Explicitly synthetic, not a Sentinel security incident or measured probability |
| 5 | Durable SQLite case lifecycle, notes, enrichment, reviewer gate, classified closure, idempotent local ticket and audit chain | One local case/nine audit events; six local failure scenarios. Human roles and remote timeouts are simulated, not authenticated SaaS operations |
| 6 | Four hash-pinned compiler-validated Bicep models, one parameter file, nineteen-target nonmutating comparison, exact/destructive-change gates and recovery runbook | Actual local compilation; no full platform redeployment/ARM what-if claimed. Existing REST/OIDC fixed-resource deployments are independently evidenced |
| 7 | Twenty customer deliverables, source-derived twelve-rule coverage, eight fictional tickets, RACI/SLIs/risks/handover | [Customer contract validation](../../customer/atlas-financial/README.md), not a real regulated customer/service certification |
| 8 | Integrated one-command demo, standalone evidence explorer, portable archive, manifest, presentation/demo/interview material and protected CI | Release capability scope is usable offline after Azure closes; original mission remains gated on Phase 1 live acceptance |

## Actual Azure baseline and cost

The read-only [eligibility record](../../evidence/completion/eligibility.sanitized.json)
and [fresh control-plane baseline](../../evidence/completion/baseline.sanitized.json)
confirm the existing pinned Enabled subscription, spending limit On, West
Europe workspace, `pergb2018`, 30-day retention and 0.1 GB/day cap. Thirteen
rules remain: twelve disabled Scheduled and original enabled Fusion. Eighteen
CI assignments were observed; the owned Arc machine was Disconnected, consistent
with the stopped guest. No new project resource, role, log query, message or
paid plan was introduced by this offline increment.

Published credit still shows EUR175.99436818021823, expiry 12 November 2026
18:00:16 UTC. Credit is not a live invoice and billing lag is possible. The
earlier AMA pilot's 2,600 billable bytes are historical, not a final monetary
charge. The user's new maximum is EUR175; no amount of available credit is a
reason to consume it. Existing unrelated workloads can incur costs independently.

## Verification and provenance

The protected PR records exact implementation head, required Python 3.12 CI
and merge SHA. Local Python 3.15 unit tests, fixed rule validation, customer
contracts, actual Bicep compilation, actionlint, relative links, JSON syntax,
staged identifier/key/token scans and diff checks are performed before merge.
Independent reviewers checked archive privacy and incident-scope/time matching;
their discovered issues were corrected and tested, not hidden as successful
cloud executions. Compiler acquisition is a public official-release download,
hash-checked again before execution; it neither authenticates to Azure nor
grants deployment authority.

Local reports may be regenerated. Historical actual evidence is preserved at
its recorded timestamp. An imported JSON label is not cryptographic proof of
Azure origin: public review, source SHA and linked actual workflow results
provide the provenance chain. A clean code test or preview is not a live event.

Actual local Chrome/Playwright checks exercised all four tabs, the severity
filter, seven-event case timeline, case expansion, both linked dashboards and
a 390px mobile viewport without horizontal overflow, JavaScript errors or
external page requests. [Browser check](../../evidence/completion/browser.sanitized.json)
and [synthetic dashboard screenshot](../../evidence/completion/dashboard.synthetic.png).

## Account closure and retained value

Keep a local clone and the portable archive, verify its manifest and open the
dashboard without Internet. Preserve private operational state separately;
never upload it as evidence. Keep the guest off and consumed pilot/bootstrap
ledgers intact. There are no schedules or repeating senders to restart later.
Account cancellation, deletion, billing-plan changes and university identity
changes are not performed by the project. The operator controls account closure
after reviewing the [handover checklist](../../customer/atlas-financial/handover.md).

If the subscription becomes disabled/expired before any separately approved
test, stop further project cloud work; record the reason and hand over the
verified offline release. Do not upgrade or switch to keep a demonstration alive.
