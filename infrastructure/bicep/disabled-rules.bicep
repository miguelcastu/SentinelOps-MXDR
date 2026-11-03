// Exact reviewed catalog; no KQL/body parameters and no enabled-rule path.
// Existing AZ-DET-001 UUID must be supplied from the private pin/inventory.
targetScope = 'resourceGroup'

@description('Existing reviewed AZ-DET-001 UUID, never a newly generated ID.')
@minLength(36)
@maxLength(36)
param diagnosticRuleId string

resource workspace 'Microsoft.OperationalInsights/workspaces@2025-02-01' existing = {
  name: 'law-sentinelops-mxdr-euw'
}

var rules = [
  { name: diagnosticRuleId, body: loadJsonContent('../../detections/azure/AZ-DET-001.json') }
  { name: '5a347e1c-bc1e-53ab-80a1-d6fd619eb91c', body: loadJsonContent('../../detections/azure/AZ-DET-002.json') }
  { name: '9816cc5e-3304-5e27-b7a2-8d4a267c812b', body: loadJsonContent('../../detections/azure/AZ-DET-003.json') }
  { name: 'f99041ea-187d-5462-9fb7-6c29f431b515', body: loadJsonContent('../../detections/azure/AZ-DET-004.json') }
  { name: '2c1170e0-1592-57b7-8b8e-bd3e0178cb0b', body: loadJsonContent('../../detections/azure/AZ-DET-005.json') }
  { name: '8e0e18f1-1d32-5c54-9f6a-98f52ef3ea6e', body: loadJsonContent('../../detections/azure/AZ-DET-006.json') }
  { name: '4045d337-3c91-50c6-9a6d-cb434cd985d6', body: loadJsonContent('../../detections/azure/AZ-DET-007.json') }
  { name: '11169c66-cfdb-5b40-94ec-4d01c3845503', body: loadJsonContent('../../detections/azure/AZ-DET-008.json') }
  { name: '765a60b1-d0e9-5cac-9baf-c790fd2e80cf', body: loadJsonContent('../../detections/azure/AZ-DET-009.json') }
  { name: '5eee8a54-76d0-53a6-8262-29b34d3bd7b9', body: loadJsonContent('../../detections/azure/AZ-DET-010.json') }
  { name: 'ed65b130-b1e9-540e-8015-b09bd9797d80', body: loadJsonContent('../../detections/azure/AZ-DET-011.json') }
  { name: 'eed467bf-df6d-5fa9-8957-6c916e680bcc', body: loadJsonContent('../../detections/azure/AZ-DET-012.json') }
]

resource analytics 'Microsoft.SecurityInsights/alertRules@2025-09-01' = [for rule in rules: {
  name: rule.name
  scope: workspace
  kind: 'Scheduled'
  properties: rule.body.properties
}]
