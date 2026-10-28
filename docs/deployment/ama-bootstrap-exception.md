# Proposed one-time AMA initialization exception

**Approval pending. This file grants no authorization.** The original limited
pilot approval allows personal administrative setup/Arc connection, but requires
the DCR, extension and association to be deployed through GitHub OIDC.

Actual Azure REST rejected the exact DCR-scoped role assignment with HTTP 404
`ResourceNotFound`, explicitly identifying the not-yet-existing DCR. Both the
CLI scope approach and direct ARM RBAC approach were tried. No group-scoped
writer was granted. The owned machine is already connected to Arc; its
read-only CI assignment exists. AMA and live ingestion remain pending.

The proposed exception is **one initialization of only these existing approved
resource targets using the current pinned personal MFA session**, from reviewed
merged main:

| Resource | Fixed target |
|---|---|
| DCR | `dcr-sentinelops-ama-linux`, existing resource group/West Europe |
| Arc AMA extension | `lab-sentinelops-linux-01/AzureMonitorLinuxAgent` |
| DCR association | `lab-sentinelops-linux-01/sentinelops-ama-linux` |

Use the same [reviewed contract](../../ama/cloud.py) and provisioning/read-back
checks as OIDC. Only local4 Warning and above, one existing workspace and no
additional source, paid plan, activation, diagnostic or billing change. Possible
ingestion charges remain within the already approved single pilot scope; this
does not authorize more data or promise a hard billing cap.

The [gated initializer](../../scripts/bootstrap_ama_resources.py) defaults to
preview and fails before authentication without a separate private record at
`.local/ama/one-time-bootstrap-approved.json` containing the exact fingerprint
and `allow_one_time_personal_bootstrap: true`. That record may be written only
after the operator explicitly approves this exception. A completion ledger
prevents using the initializer again after success. Partial failure preserves
reviewable fixed resources; no deletion, broader grant or automatic sender.

After initialization, run the existing administrative RBAC setup to attach
only the four exact-resource assignments. Then dispatch the protected main
OIDC workflow, which must verify actual persisted matching resources and the
unchanged workspace/rule inventory. Future routine verification/deployment
continues through OIDC; the personal exception is not permanent. Execute the
already approved ten-message pilot once, aggregate verification at most three
times, and gracefully stop the guest, including on failure.

This avoids giving CI write permission across all DCRs in the resource group
or all extensions on the machine. It adds no identity or service-principal
secret, changes no MFA rule, and does not upgrade/switch the subscription.
If the exception is declined, leave the owned guest stopped and report that
Arc is connected but AMA ingestion is not complete.
