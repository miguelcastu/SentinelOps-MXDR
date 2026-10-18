# Disabled scheduled-rule template

The template supplies the verified Scheduled REST structure, disabled state, PT15M/PT1H schedule, explicit grouping defaults and resource/IP output mapping. Its placeholder name and no-match query are deliberately rejected by the approved detection validators; it cannot be deployed directly by these workflows.

To propose another detection, use an existing approved data source, replace the query and documentation, select parent MITRE technique IDs (T####), add positive/negative/edge and benign-match fixtures, define a separate constrained schema and register its reviewed ID in the validator. Obtain an exact resource target and least-privilege assignment through the approved setup process. Then submit the feature branch for protected PR validation.

Copying a template does not authorize new connectors, infrastructure, rule activation or broader permissions. Keep the rule and incident creation disabled. A synthetic test pass does not establish real false-positive performance.
