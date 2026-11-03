# Phase 6: IaC, preview and recovery validation

Validated locally on **3 November 2026**. This increment executed no Azure write,
ARM what-if, platform deployment, role change, log query, guest boot or upload.
Existing actual OIDC REST evidence stays a separate evidence class.

The official Windows x64 **Azure/bicep 0.48.1** binary was downloaded to ignored
`.local/tools/`, checked against the official release digest, then checked again
by the wrapper before execution. SHA-256:

`398af294cf16ac4becdbd008a77d148d0e8e91492309a6b60ec911b7e1cab082`

[Pinned release/OS digests](../../infrastructure/bicep/tools.lock.json).
Acquiring an offline compiler is not an Azure deployment.

```powershell
python -m infrastructure.preview --bicep .local/tools/bicep-v0.48.1.exe
python -m unittest discover -s tests -p test_infrastructure.py -v
```

| Check | Actual result | Meaning |
|---|---|---|
| Compile/lint | Four templates plus one parameter file; `--no-restore`; no diagnostics | Actual compiler execution, not a mock |
| Foundation/export | Zero writable resources in compiled models | References do not independently prove current existence |
| AMA | Three bodies equal `ama.cloud.contract()` | Exact collection/destination/extension/association agreement |
| Analytics | Twelve compiled fixed targets/bodies match reviewed JSON, all disabled | No query/body/activation parameter |
| Parameters | Fictional existing-rule UUID compiled privately | Does not create a real target |
| Default preview | Nineteen Unknown, zero Azure calls | No-input render is not a health assertion |
| Synthetic comparison | Nineteen Matching, explicitly synthetic | Local deterministic proof only |
| Behavioral tests | Eleven pass, including two real compiler tests | Drift, missing/duplicate/wrong scope/type, widened collection, cap changes and activation covered |
| Change gate | Create/delete/replace, foundation and nonexact changes refused | Successful review still is not deploy approval |

The first compiler pass rejected the decimal literal used to describe the cap;
it was corrected to `json('0.1')`, preserving the invariant without making the
workspace writable. Subsequent compilation passed. Compiler-dependent tests
explicitly skip when the locked binary is absent; the explicit compile step
reproduces this evidence on a fresh workstation. Standard dependency-free tests
still validate contract comparisons and destructive-change gates.

The existing [portfolio OIDC run](https://github.com/miguelcastu/SentinelOps-MXDR/actions/runs/39235924991)
verified ten additional disabled definitions, and [AMA OIDC run](https://github.com/miguelcastu/SentinelOps-MXDR/actions/runs/40774219658)
verified three already-matching resources. They demonstrate the authorized
fixed REST path, **not Bicep platform deployment**. Initial AMA creation used
the approved one-time personal exception, now consumed.

The [dated actual RBAC audit](../../evidence/local-linux-ama/preservation.sanitized.json)
has seven custom role definitions/eighteen assignments; it does not establish
group/subscription ARM deployment permission. No Contributor/Owner grant,
identity/trust duplication or environment change was introduced by this work.
The [preview](../../infrastructure/preview.py) keeps snapshot identifiers private,
uses finite bounds and never asserts input provenance. It is not ARM what-if.
[Recovery](../deployment/recovery.md) covers cold replay, fixed-target restore,
reviewed rollback, backup limits and account-close handover. No destructive
restore or disaster failover was performed.

The supported architecture is represented and genuinely compiler-validated;
approved fixed-resource deployments have historical actual Azure verification.
Full platform redeployment/ARM what-if remains **unverified**. New ARM roles or
foundation writes need separate scope/approval. The artifacts provide useful
IaC/recovery practice without claiming certified production disaster recovery.

## Additional read-only live-verification implementation

The new [manual protected-main workflow](../../.github/workflows/verify-infrastructure.yml)
and [GET-only adapter](../../scripts/verify_infrastructure.py) can compare the
compiled contracts to current Azure responses using **existing permissions**.
No cloud call was made while implementing these files. The implementation and
tests are not themselves an actual successful workflow run; final delivery must
link the actual run/report separately if it is executed.

Pre-login verification genuinely runs the locked compiler via
`scripts.check_bicep` and validates its exact result. The adapter then reads six
fixed endpoints: workspace, rules inventory, owned machine and the three AMA
children. It compares fifteen compiled writable bodies plus workspace/machine
reference contracts, accepting an intentionally Disconnected Linux guest.
Onboarding metadata and the subscription export stay Unknown and are never
queried with ungranted permissions. No live KQL, events, new grants, source
activation or resource modification is involved.

```powershell
python -m unittest discover -s tests -p test_infrastructure_live.py -v
```

**Seven additional local tests pass**, covering the exact six GETs / expected
17 Matching and 2 Unknown under mocks, disconnected-machine semantics, independent
destination UUID validation, drift/missing-rule failures, duplicate/partial/wrong
scope rejection, transport refusal of every write/unapproved route, sanitized
403 errors and compiler-evidence refusal before authentication. Tests also
check that neither actual-shaped resource IDs nor private sample values reach
the public report. They never publish mock output as real cloud evidence.
Actionlint passes the new workflow; it has no schedule or deployment path.

This path can establish current compiler-to-live contract agreement without
the unrelated permissions needed by ARM what-if. Even after a successful run,
full ARM deployment/what-if and current telemetry/runtime health remain outside
that proof. Existing resource IDs, pricing, retention, cap and rule states are
only read; the local VM remains stopped.

## Actual accepted compiler-to-live OIDC proof

[Run41700706739](https://github.com/miguelcastu/SentinelOps-MXDR/actions/runs/41700706739)
succeeded at 19:10:40UTC. Actual hash-pinned Bicep compilation preceded login;
six existing-authority GETs matched17core targets,0 Drift/0 Missing and2 explicit
Unknown (Sentinelonboarding/diagnosticexport not queried). The Arc guest was
Disconnected; no boot/write/role/query/ingestion occurred.
[Actual record](../../evidence/completion/infrastructure.sanitized.json).
This is the verified equivalent nonmutating fixed-contract preview, not a
full ARMdeployment/what-if or a destructive recovery test. The final access
audit is10 roles/22 assignments, including separately authorized lifecycle scope;
earlier7/18counts are pre-lifecycle historical checkpoints.
