# Final acceptance: SentinelOps MXDR v1.0.0

**All eight engineering phases are delivered and accepted within the documented
lab scope on 3 November 2026.** This is a personal engineering lab for fictional
Atlas Financial, not a production MXDR service or a real customer engagement.

The [release and portable archive](https://github.com/miguelcastu/SentinelOps-MXDR/releases/tag/v1.0.0)
are published after final protected CI. The release records the exact merge,
checks and archive digest. Dated cloud evidence and the offline demonstration
remain available after the operator closes Azure access.

## Reproduce without Azure

```powershell
python -m unittest discover -s tests -v
python -m scripts.validate_detection
python customer/atlas-financial/validate.py
python -m lab --bundle
```

Python 3.12+ and Git are sufficient for default offline behavior. Open
`.local/lab/index.html` for the catalog, health/risk explorers, case/audit
exports and evidence views. No authentication, network request, cloud operation
or paid dependency is needed. The ZIP contains allowlisted tracked source and
workflows, generated public reports, the explicitly reviewed synthetic
screenshot and a per-file SHA-256 manifest. It excludes unrelated private files,
credentials, VM disks, SQLite databases and unallowlisted raw Azure images.

The normalization sample, synthetic RBA finding and isolated real-scheduler
input are distinct exercises. The canonical RBA finding reaches local SOAR
with its original seven-event lineage; that local finding is not presented as
the cause of the separate actual Azure incident.

## Acceptance by phase

| Phase | Delivered and verified | Explicit limit |
|---|---|---|
| 1. Detection and incident lifecycle | Twelve deployed disabled definitions, sixty portfolio controls, actual Kusto execution of all twelve queries, and one actual scheduled alert/incident investigated and classified closed | Dedicated LAB event is synthetic; no production accuracy or activation of the twelve security rules is claimed |
| 2. Advanced ingestion | AzureActivity export/arrival, ten unique owned Linux Arc/AMA Syslog messages, and offline synthetic schema/normalizer/bounded client | Guest stopped; native SSH excluded; optional synthetic custom table remains undeployed |
| 3. Platform health | Three-source inventory/policies, sixteen safe faults, maintenance/stale/partial handling, prior OIDC health audit and current configuration evidence | Unmeasured telemetry, latency and runtime remain Unknown; no automatic fresh AMA query |
| 4. Risk correlation | Canonical identity joins, source lineage, strict sequence, deduplication/decay/caps, maintenance context and nine scenarios | Synthetic finding, not a calibrated probability or actual attack |
| 5. SOAR | Durable case, notes/enrichment, reviewer gates, classification, idempotent ticket, chained audit and six failure scenarios | Local actors and remote timeouts are simulated; no Logic App, paid SaaS or containment |
| 6. IaC and CI/CD | Four compiler-validated Bicep models, one parameter file, nineteen-target preview/recovery guard and 17 actual OIDC contract matches | Two unqueried references remain Unknown; full ARM deployment/what-if was not executed |
| 7. Customer operations | Twenty mapped deliverables, twelve definition-derived coverage records, eight fictional tickets, RACI, SLIs, risks and handover | Fictional service package, not certification or customer employment |
| 8. Portfolio delivery | Integrated explorer, portable archive/hash manifest, presentation material, actual/synthetic evidence and protected release delivery | Accepted engineering lab; no continuously operated security-service claim |

## Actual verification paths

- [Scheduled lifecycle](lifecycle.md): one match, alert and incident; detailed
  read-only investigation; OIDC classification as Closed / BenignPositive /
  SuspiciousButExpected at 19:33:13 UTC. Creation and resource changes used
  OIDC; the approved personal session inspected details read-only. Defender
  link presence is verified, but the portal UI was not opened.
- [Final lifecycle reconciliation](../../evidence/completion/lifecycle-start.sanitized.json):
  OIDC run [41709469491](https://github.com/miguelcastu/SentinelOps-MXDR/actions/runs/41709469491)
  restored first/last activity to the verified 19:12:41 source time on the
  already closed incident, then verified it at 20:07:05. This operation included
  **one exact-incident PUT**. It preserved classification and did not create
  another event or reactivate the rule; it was not a purely read-only run.
- [Twelve-query KQL runtime](live-kql-portfolio.md): one one-hour aggregate POST.
  AZ-DET-002 matched 3 rows, AZ-DET-003 matched 2, and the other ten matched 0.
  Counts may reflect legitimate setup. No raw rows or identities were returned;
  the attempt ledger remains consumed. This is not a false-positive rate.
- [Compiler-to-live comparison](../../evidence/completion/infrastructure.sanitized.json):
  four compiled models/one parameter file compared through six GETs, producing
  17 Matching, 0 Drift, 0 Missing and 2 Unknown. The stopped Arc guest remained
  stopped. This verifier made no resource write, role change or log query.
- [Final preservation audit](../../evidence/completion/final-preservation.sanitized.json):
  74 baseline/preservation checks plus two post-reconciliation timeline checks,
  completed at 20:10:19 UTC. The original thirteen rule properties, subscription,
  workspace controls, CI identity and immutable trust are preserved. There are
  14 unique rules, 22 exact assignments and 10 validated custom roles. No broad
  writer, wildcard, table-data or CI role-management grant was added.
- [Historical AMA proof](../../evidence/local-linux-ama/ingestion.sanitized.json):
  ten unique messages, 900 payload bytes and 2,600 billable bytes, reconciled
  through two aggregate queries. The guest is off; this is neither a current
  heartbeat nor a final monetary charge.
- [GitHub closeout](../../evidence/completion/github-closeout.sanitized.json):
  the lifecycle approval gate, recovery/reconciliation references and exact-incident
  identifier secret were removed. Existing Azure OIDC configuration and all
  22 Azure assignments were preserved. The completed test is disarmed.

## Checks and evidence quality

**213 local tests pass**, including actual compiler checks. Required Python 3.12
CI runs the suite, validators, customer contracts, integrated replay, archive
checks and the pinned Linux Bicep compiler. Independent checks cover SOAR JSON
Schema, workflow lint, links, archive privacy/CRC/hash manifest, and browser
behavior: tabs, severity filtering, source lineage, linked dashboards and a
390 px mobile viewport.

Mock results are not published as actual cloud evidence. Public source SHAs,
workflow links and independent REST observations provide the provenance chain.
JSON digests bind the reports to their inputs; they are not cryptographic Azure
attestations. Earlier authorization failures remain in the history. The detailed
investigation and original incident snapshot are separate from OIDC creation,
classification and the later timestamp repair.

## Subscription, cost and resource scope

The existing subscription and plan remain Enabled with spending limit On.
Workspace `pergb2018` pricing, 30-day retention, the 0.1 GB/day cap, budgets and
diagnostics are preserved. Published credit is EUR 175.99436818021823, expiring
12 November 2026 at 18:00:16 UTC. Closed balances can lag usage. The operator's
EUR 175 maximum was a ceiling, not a spending target; the final monetary charge
remains unknown. Spending protection is not a custom per-test euro cap.

Completion introduced one fixed LAB rule, three narrow role definitions/four
exact assignments, one scheduled alert and one incident classified closed.
The final inventory contains twelve disabled managed definitions, the disabled
LAB test and original enabled Fusion. No existing resource was deleted. No
Azure VM, paid add-on, university source or new live ingestion batch was added,
and no ongoing sender or enabled managed test rule remains.

Resource-group inventory found no Azure VM, Logic App, app or database type in
the inspected scope. This is not a tenant-wide inventory or proof that every
Defender plan is free; global Defender pricing was not established and no
Defender plan was enabled by this work. Existing unrelated workloads may still
incur costs.

## Handover and scope freeze

Keep a local clone, verify the archive manifest and open the demo without the
Internet before operator-led Azure closure. Private keys, pins and consumed
ledgers remain separate. The local guest stays off, and completed tests are not
replayed. See the [operator handover](../../customer/atlas-financial/handover.md).

No required engineering task remains within this accepted lab scope. Native
authentication collection, active-rule tuning, a custom-table deployment, full
platform redeployment/disaster recovery and paid automation are future scope,
not hidden acceptance claims. They require separate permissions and cost review.
After credit expiry, preserve the release rather than upgrading or switching.

Account cancellation remains the operator's choice. This project has not
cancelled the account, deleted Azure resources or changed the university
identity/directory.
