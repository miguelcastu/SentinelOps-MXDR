# Completed one-time AMA initialization exception

**Explicitly approved on 28 October 2026:** the operator answered
"Autorizar esa inicialización única de los tres recursos" after reviewing
PR #16. The original limited
pilot approval allows personal administrative setup/Arc connection, but requires
the DCR, extension and association to be deployed through GitHub OIDC.

Actual Azure REST rejected the exact DCR-scoped role assignment with HTTP 404
`ResourceNotFound`, explicitly identifying the not-yet-existing DCR. Both the
CLI scope approach and direct ARM RBAC approach were tried. No group-scoped
writer was granted. The owned machine is already connected to Arc; its
read-only CI assignment existed at that checkpoint. The approved exception
subsequently completed at 21:41:24 UTC; [actual initialization evidence](../../evidence/local-linux-ama/initialization.sanitized.json).
Exact-resource RBAC, main OIDC verification and ten-message Syslog acceptance
then succeeded. The guest is stopped; [final validation](../validation/local-linux-ama.md).

The approved exception is **one initialization of only these existing approved
resource targets using the current pinned personal MFA session**, from reviewed
merged main:

| Resource | Fixed target |
|---|---|
| DCR | `dcr-sentinelops-ama-linux`, existing resource group/West Europe |
| Arc AMA extension | `lab-sentinelops-linux-01/AzureMonitorLinuxAgent` |
| DCR association | `lab-sentinelops-linux-01/sentinelops-ama-linux` |

The execution used the same [reviewed contract](../../ama/cloud.py) and provisioning/read-back
checks as OIDC. Only local4 Warning and above, one existing workspace and no
additional source, paid plan, activation, diagnostic or billing change. Possible
ingestion charges remain within the already approved single pilot scope; this
does not authorize more data or promise a hard billing cap.

The [gated initializer](../../scripts/bootstrap_ama_resources.py) defaults to
preview and fails before authentication without a separate private record at
`.local/ama/one-time-bootstrap-approved.json` containing the exact fingerprint
and `allow_one_time_personal_bootstrap: true`. That record may be written only
after the operator explicitly approves this exception, as now recorded for
this execution. A completion ledger
prevents using the initializer again after success. Partial failure preserves
reviewable fixed resources; no deletion, broader grant or automatic sender.

The completed post-initialization sequence used administrative RBAC setup to attach
only the four exact-resource assignments. The protected main
OIDC workflow subsequently verified actual persisted matching resources and the
unchanged workspace/rule inventory. [Successful OIDC run](https://github.com/miguelcastu/SentinelOps-MXDR/actions/runs/40774219658).
Future routine verification/deployment continues through OIDC.
The approved ten-message pilot ran once, reconciled on the second aggregate
query, and the guest shut down gracefully. Both completion/attempt ledgers are
consumed: do not delete/reset them or rerun personal bootstrap or the sender.
The exception is completed, not a reusable personal deployment route.

This avoids giving CI write permission across all DCRs in the resource group
or all extensions on the machine. It adds no identity or service-principal
secret, changes no MFA rule, and does not upgrade/switch the subscription.
No further personal initialization or collection expansion is authorized.
