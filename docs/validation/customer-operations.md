# Customer operations and portfolio validation

Implemented on **3 November 2026** as a fictional customer/portfolio package.
No Azure request, deployment, source activation, recipient notification, account
closure or chargeable service is introduced by this component.

## Implemented artifacts

The [Atlas Financial package](../../customer/atlas-financial/README.md) supplies
twenty mapped customer deliverables: discovery, security requirements,
monitoring scope, architecture, RACI, source onboarding, detection/MITRE
coverage, catalog, runbooks, triage/response, health/cost/KPI definitions,
change/escalation, acceptance, risk and handover. Its eight structured example
tickets cover onboarding, connector failure, tuning, investigation, deployment
failure, automation, cost and drift. Each has a trigger, investigation,
root cause, actions, measurable closure criteria and evidence limitations.

The [portfolio guide](../portfolio/README.md) includes a timed five-minute
demonstration, fifteen-minute presentation, interview/CV wording, engineering
trade-offs and six evidence-linked troubleshooting cases. CV wording does not
imply a real financial customer or production security service.

## Repeatable validation

```powershell
python customer/atlas-financial/validate.py
```

The dependency-free validator:

- Requires exactly twelve distinct reviewed coverage records and compares their
  title, severity, tactics, techniques, schedule, lookback, disabled state and
  incident setting to the versioned Azure rule bodies.
- Requires eight distinct ticket categories and explicitly fictional, synthetic
  closure states; rejects missing/substantively empty investigation fields.
- Maps twenty unique deliverables to real public repository files and rejects
  missing/absolute/private/out-of-repository artifact paths.
- Keeps actual live incident acceptance outside the customer's offline package.
  It never interprets a local case as a Sentinel incident or invents a cloud result.

Relative Markdown links and JSON parsing are checked during integration. The
required project unit tests and detection validation remain part of the final
repository checks; their current counts are recorded by final CI/status rather
than frozen into this documentation.

## Evidence and limitations

The coverage catalog is a **versioned-definition summary**, not a new Azure
query. Historical actual deployment, RBAC and AMA aggregate/shutdown records
are referenced by date. Every service ticket is a fictional exercise, even
when it cites a real engineering method or sanitized historical lab observation.
Synthetic targets/response times are not measured service SLAs. No production
precision/recall, licensed identity source, native SSH coverage or real customer
endorsement is claimed.

This component completes the offline customer operations deliverables and
portfolio presentation material. The original mission's actual scheduled
alert -> incident -> investigation -> classification gate must be assessed
from the [current global status](../PROJECT_STATUS.md) and its actual evidence;
the presence of these documents or synthetic closed tickets cannot satisfy it.
