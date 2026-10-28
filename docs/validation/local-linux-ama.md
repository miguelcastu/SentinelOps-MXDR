# Local Linux / Arc / AMA pilot validation

The explicitly approved one-machine pilot completed on **28 October 2026**.
One cloud batch reconciled in Kusto; the local VM is now powered off.
This is a bounded transport proof, not continuous monitoring or active detection.
See the [onboarding and operation runbook](../onboarding/local-linux-ama.md).

## Actual acceptance evidence

All times below are UTC. Public records contain counts and configuration facts,
not raw Syslog rows, private machine/run IDs, account identities or tokens.

| Stage | Actual result | Evidence |
|---|---|---|
| Local preparation | Official hash-checked Ubuntu 24.04.5 OVA; one vCPU, 1,536 MiB RAM; completed cloud-init; key-only SSH; rsyslog active | [Preparation snapshot](../../evidence/local-linux-ama/preparation.sanitized.json) |
| Arc registration | One owned machine Connected at 21:03:24; system-assigned machine identity, Arc package 1.69.03579.1568 | [Arc observation](../../evidence/local-linux-ama/arc-onboarding.sanitized.json) |
| One-time personal initialization | Same fixed DCR, AMA extension and association persisted; completed at 21:41:24 under the separately approved exception | [Initialization](../../evidence/local-linux-ama/initialization.sanitized.json) |
| Protected main OIDC verification | All three targets already matching; no creation, messages or log queries in this run | [OIDC REST evidence](../../evidence/local-linux-ama/oidc-configuration.sanitized.json) |
| Preservation and access audit | Same pin, pricing, retention and cap; thirteen unchanged rules; four narrow AMA assignments, eighteen total; no broad writer or new CI query access | [REST/RBAC audit, 21:51:35](../../evidence/local-linux-ama/preservation.sanitized.json) |
| Live Syslog acceptance | **10 total / 10 distinct**, **2,600 billable bytes**, latest event 21:50:00; successful query 21:55:02 | [Actual Kusto aggregate](../../evidence/local-linux-ama/ingestion.sanitized.json) |
| Shutdown | Graceful guest shutdown; VirtualBox `poweroff` at 21:58:02 | [Hypervisor read-back](../../evidence/local-linux-ama/shutdown.sanitized.json) |
| Post-pilot finances/settings | Enabled subscription, spending limit On; published EUR 175.99436818021823; `pergb2018`, 30 days, 0.1 GB/day unchanged | [Financial check, 21:58:34](../../evidence/local-linux-ama/financial.sanitized.json) |

The actual AMA extension version was **1.45.1**, provisioning Succeeded. The
DCR also reported Succeeded. The association API did not report a provisioning
state: matching actual association metadata and successful collection establish
the binding, rather than inventing a Succeeded field. Background extension
automatic upgrade is disabled; minor-version resolution was allowed during
initial installation.

## Single batch and Kusto boundary

The guest emitted **one batch of ten** labeled synthetic local4.warning
messages with tag `sentinelops-lab`, **900 message bytes**, within the approved
4,096-byte allowance. The downloaded AMA config contained local4 before sending.
Local rsyslog and its AMA forwarding listener were verified without exposing
the event text. The persistent attempt ledger remains consumed: do not resend
or reset it because a later query is slow.

The fixed [one-hour KQL](../../ama/validation.kql) filters the exact private
machine/run, facility and tag, and returns only count, distinct count, last-seen
and billable bytes. Actual Kusto execution occurred twice: 21:52:01 returned
zero; 21:55:02 returned ten total and ten distinct. The third permitted query
was unnecessary and was not executed. No raw row was returned. This proves
arrival and reconciliation for this run; it is not a latency benchmark, proof
of unlimited retention, native attack test or production false-positive rate.

An earlier **local-only** ten-message preparation check ran before Arc/AMA.
Its historical local log counts do not represent a second cloud pilot. The
cloud aggregate reconciles only the later unique run. Neither this source nor
the twelve disabled AzureActivity definitions provides active Linux alerting.

## Initialization, OIDC and protected delivery

Azure rejected RBAC against the absent DCR with actual HTTP 404
`ResourceNotFound`. CLI and direct ARM approaches were tried; no resource-group
writer was granted. The operator then explicitly approved [PR #16's one-time
personal initialization](../deployment/ama-bootstrap-exception.md). Its separate
private approval and completion ledger were honored. Some fixed resources were
created during bounded attempts; final completion reused the matching DCR and
extension and created the association. This was personal initialization,
**not OIDC resource creation**.

After exact-resource RBAC setup, [main OIDC run
40774219658](https://github.com/miguelcastu/SentinelOps-MXDR/actions/runs/40774219658)
at source `e2a2439ea785a1ace7b3554b272c4b4bad176acb` independently verified
all three persisted contracts and unchanged workspace/rules. Ownership tags
identify the routine OIDC manager; they do not change the initial auth history.
Four new narrow role definitions/assignments reuse the existing CI identity
and immutable federation. Their exact read/write actions and scopes are in
the audit record; no deletion, billing, broad collection or new CI log-query
permission was added. The live aggregate used the approved personal session.

Local preparation was reviewed in PR #13, cloud tooling in PRs #14-16, and
the strict Azure read-back compatibility fix in [PR
#18](https://github.com/miguelcastu/SentinelOps-MXDR/pull/18), implementation
`31a206a`, merge `e2a2439`. Its [required Python 3.12
CI](https://github.com/miguelcastu/SentinelOps-MXDR/actions/runs/40771934419)
passed before cloud verification. Current evidence/documentation delivery uses
the same protected PR path; it needs no new Azure deployment.

## Troubleshooting that preserved scope

- **Guest boot:** two-vCPU boot panicked; minimal paravirtualization stalled.
  One vCPU with KVM paravirtualization and APIC/x2APIC booted with Windows
  hypervisor protection preserved. The underlying kernel issue was not diagnosed.
- **DCR read-back:** Azure added a read-only destination `workspaceId`.
  PR #18 compares it to independently read existing-workspace metadata while
  still rejecting a wrong ID, extra destinations or unknown fields. No target
  or approved fingerprint changed.
- **Slow extension:** the roughly 606 MB package downloaded/unpacked slowly on
  one vCPU. A bounded client poll expired and an immediate child-resource GET
  briefly returned HCRP404. Private guest checks and later actual REST showed
  the existing operation progressing; it was resumed without another creation
  request, broader permissions or a paid machine.
- **Configuration propagation:** AMA initially requested config before the
  association existed. After binding, the downloaded local4 config was still
  absent. Restarting only the guest's `azuremonitoragent` service refreshed
  its config; the sender waited for readiness. No extra DCR or test batch.
- **Initial zero rows:** rsyslog's forwarder and AMA listener were healthy.
  Waiting for the second bounded aggregate query reconciled ten messages;
  the sender was never replayed.

Microsoft's [Linux AMA troubleshooting](https://learn.microsoft.com/azure/azure-monitor/agents/azure-monitor-agent-troubleshoot-linux-vm)
and [rsyslog diagnostics](https://learn.microsoft.com/azure/azure-monitor/agents/azure-monitor-agent-troubleshoot-linux-vm-rsyslog)
explain the service/configuration/forwarding checks. Raw diagnostics remain
ignored. No Azure resource was deleted to recover.

## Local verification and limitations

- `python -m unittest discover -s tests -v`: **143 tests pass** locally on
  Python 3.15 and in required Python 3.12 CI / the OIDC run.
- `python -m scripts.validate_detection`: both restricted disabled contracts
  pass; portfolio validation also checks ten additional fixed definitions.
- Offline AMA rendering, actionlint 1.7.12, changed documentation links,
  evidence privacy checks and `git diff --check` pass.
- Mock tests cover fixed-resource ownership, complete DCR/destination checks,
  independently checked read-only metadata, exact RBAC and default-preview /
  missing-consent refusal. They are separate from actual REST/Kusto evidence.

No Azure VM, custom table, Entra export/device join, university telemetry,
Defender/Insights/Update Manager plan, rule activation or incident was added.
Three existing local VMs and host security settings were preserved. The policy
preflight found existing MFA and AzureActivity export assignments, with no
identified add-on deployment policy. Defender pricing returned 404 while
Microsoft.Security was NotRegistered; its full plan state remains unverified.
No provider/plan was enabled to work around that inspection limitation.

The post-pilot credit report is a **published closed balance**, expiring
12 November 2026 18:00:16 UTC; it can lag usage. The **2,600 billable bytes are
not a measured final monetary charge** or a guarantee of zero spend. Existing
unrelated workloads may still accrue charges. No subscription, plan, pricing,
retention, daily cap, budget or diagnostic setting was changed.

The VM is powered off, so this source has no continuous freshness guarantee;
its installed services/DCR would resume at boot. Only local4 Warning and above
is selected. Native SSH/authpriv, process, Windows/Sysmon and network detections
are not covered. The [separate source inventory](../../ama/source.json) records
verified acceptance; the existing health evaluator has no AMA freshness policy
or automatic collector. Historical [RBAC blocker](../../evidence/local-linux-ama/rbac-boundary.sanitized.json)
and [pending-approval shutdown](../../evidence/local-linux-ama/pending-approval-shutdown.sanitized.json)
remain dated checkpoints, superseded by the current evidence above. Another
batch, broader collection or active alerts require a separate approved scope.
