# Azure and Sentinel deployment record

**Method:** manual Azure Portal provisioning, 13 October 2026. This is a factual record, *not* an IaC implementation.

1. Create `rg-sentinelops-mxdr` in the Azure lab subscription.
2. Create the Log Analytics workspace `law-sentinelops-mxdr-euw` in West Europe. A prior attempt at Spain Central was not Sentinel-compatible in the user's workflow; workspace region cannot be changed in place.
3. Enable Microsoft Sentinel on that workspace. Confirm the Sentinel solution/resource appears in the resource group.
4. Confirm access through the Defender portal and verify budget alerts and estimated Azure consumption.
5. Check Log Analytics billing tier, retention and daily cap through Azure Portal; the supplied screenshots **do not independently prove exact retention or daily-cap values**.
6. Proceed with the [Azure Activity connector](../onboarding/azure-activity.md).

## Cost caveats

Subscription promotional credit does not imply indefinite free service. Budget alerts do not automatically shut down resources; daily Log Analytics caps affect eligible ingested data only, and can reduce security visibility. Before moving the lab to pay-as-you-go, explicitly check current billing, charges and expiry. Avoid paid Marketplace offerings, unnecessary VMs and optional features.

At teardown, review subscription-scoped diagnostic settings and Azure Policy assignment as well as the resource group: **removing the group alone does not necessarily remove these subscription-scoped objects**.

Evidence: [Azure resources](../../evidence/01-azure-resources.png).
