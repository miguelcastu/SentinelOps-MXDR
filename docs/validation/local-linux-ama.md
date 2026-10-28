# Local Linux machine / AMA preparation validation

Observed on **28 October 2026**. This record covers actual local VM work and
offline cloud configuration. It is not a completed Azure source onboarding.
The [runbook](../onboarding/local-linux-ama.md) contains the design, manual
operation, cloud rollout proposal, budget controls and acceptance conditions.

## Actual evidence

[Sanitized preparation evidence](../../evidence/local-linux-ama/preparation.sanitized.json)
contains separate guest, local Syslog and shutdown observations:

| Stage | Result | Evidence boundary |
|---|---|---|
| Host ownership | Operator confirmed personal PC and authorized local VM | No university-managed endpoint is used |
| Image | Official Ubuntu OVA; published SHA-256 matched, 590,766,080 bytes | HTTPS manifest comparison, not an independently verified GPG signature |
| VM | Created only `lab-sentinelops-linux-01`; 1 vCPU / 1,536 MiB | Local VirtualBox, no Azure VM |
| Boot/guest | Ubuntu 24.04.5 LTS x86_64; cloud-init done | Actual SSH probe, 20:34:53 UTC |
| SSH | Active; password, keyboard-interactive and root login disabled | Effective `sshd -T` policy checked |
| Syslog | rsyslog active; ten total / ten distinct pilot messages reconciled | Local `/var/log/syslog` only, 20:32:48 UTC |
| Local pilot | local4.warning, tag `sentinelops-lab`, 900 message bytes | Labeled synthetic messages; no native attack or real authentication test |
| Arc package | Installed, version `1.69.03579.1568`, **Disconnected** | Agent's actual local JSON response; not an Azure registration |
| AMA | Not installed | No collection extension or cloud destination |
| Shutdown | **poweroff**, 20:35:19 UTC | Actual VBoxManage read-back after graceful shutdown |
| Isolation settings | NAT; loopback SSH; clipboard/drag-drop disabled; zero shared folders | Actual hypervisor read-back; NAT still permits outbound connections |

Three pre-existing VMs were left intact. No host hypervisor installation,
reboot, global SSH change, security-policy relaxation or paid local software
was required. The original two-vCPU guest panicked, a minimal-paravirtualization
attempt stalled, and the final one-vCPU/APIC/KVM configuration booted. These
are observed attempts; the underlying virtualization bug was not diagnosed.

The first local Syslog wrapper attempt stopped before sending when systemctl
returned exit 1 for an absent AMA unit. After handling that expected absence,
the single successful batch reconciled all ten messages. No Azure ingestion
retry or cloud sender was executed.

## PR #13 preparation snapshot and unchanged boundaries

At the PR #13 local-preparation checkpoint, no Arc registration, AMA extension, DCR, DCR association, table, connector,
role, identity, Azure VM, diagnostic change, rule activation or cloud ingestion
was performed. No KQL query was executed. Existing subscription, plan, budget,
workspace pricing, retention and cap were not changed. Local verification's
`azure_requests: 0` fields describe those local commands; separate read-only
Azure provider/credit inspection was performed for the proposed cloud plan.

The read-only credit observation was EUR **175.99436818021823**, with expiry
**12 November 2026 at 18:00:16 UTC**. This is a published closed balance and
can lag usage. It does not prove that existing Azure workloads have no charges
or establish a guaranteed price for a future AMA pilot.

All three Arc prerequisites were NotRegistered when inspected:
`Microsoft.HybridCompute`, `Microsoft.GuestConfiguration` and
`Microsoft.HybridConnectivity`. Microsoft.Insights was Registered. No provider
registration was attempted. Tenant policies, inherited add-on deployments,
permissions for a new source and live billing effects are still pending review.

## Local code validation

- Required `python -m unittest discover -s tests -v`: **134 tests pass** on
  local Python 3.15, including four new AMA boundary cases.
- Required `python -m scripts.validate_detection`: both restricted disabled
  rule contracts pass; the ten-rule portfolio remains separately validated.
- `python -m ama` and `python -m ama --render-private`: plan and fixed bodies
  rendered offline; the private subscription identifier stays under `.local/`.
- actionlint **1.7.12** passes all seven workflows; published release checksum
  verified. Changed documentation links and `git diff --check` pass.
- Local preparation/installer/Syslog commands default to preview. The installer
  SHA-256 is pinned, never runs `connect`, and writes raw diagnostics privately.
- DCR tests reject wildcard collection, Info severity, an extra stream or
  destination, another resource group/workspace and malformed resource paths.
  Pilot tests enforce ten unique messages, a finite byte allowance and reject
  unsafe, too-long or invalid run IDs.

The one-hour [aggregate KQL](../../ama/validation.kql) is proposed and has not
been executed by Kusto. Local Python tests are not KQL runtime validation.
There is no measured AMA latency, billable volume, production false-positive
rate, active endpoint detection, Sentinel alert or incident evidence.

## Remaining acceptance

Subsequent approved execution: the three Arc providers are now Registered.
At **21:03:24 UTC**, the local Arc agent and actual Azure REST both confirmed
the one owned machine Connected. Its system-assigned machine identity is part
of Arc onboarding, not a university device join. AMA, DCR and live messages
remain pending. The administrative RBAC setup stopped when Azure CLI attempted
to inspect a resource that had not yet been provisioned. The fix lists the
existing principal's assignments through ARM and creates only deterministic
exact-resource assignments; it adds no action or broader scope. Two regression
tests cover future-resource/idempotent setup and duplicate/wrong-principal stops.

The operator explicitly approved the concrete [cloud exception](../onboarding/local-linux-ama.md)
after reviewing PR #13. Local preparation was merged as `344e1fb` after
[required Python 3.12 CI](https://github.com/miguelcastu/SentinelOps-MXDR/actions/runs/40765499479).
The follow-up implementation adds five mock-tested cloud boundary cases
(139 total), a manual main-only OIDC configuration workflow, preview-first
provider/RBAC setup, one-time local Arc authentication and a single-attempt
local sender with at most three aggregate queries. Mock deployment output is
suppressed in tests to avoid presenting it as actual Azure evidence.

Policy preflight identified only the two existing MFA enforcement policies and
the existing AzureActivity export policy. Defender pricing inspection returned
404 with Microsoft.Security NotRegistered; that plan state remains unverified,
and no security provider/plan is enabled to work around it. Fresh closed credit
still reported the same amount and expiry, with billing lag possible.

Complete protected review/CI/merge of the OIDC deployment path and
minimum permissions, register/connect the one machine, provision/read back AMA
and its DCR, then reconcile one unique ten-message run by aggregate query.
Only then mark this source active, extend platform-health policies and design
native Linux detections. Keep the VM stopped while that rollout is pending.
