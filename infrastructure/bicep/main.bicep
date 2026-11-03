// Architecture inventory only: no resources are created or updated by this file.
// An ARM deployment record would still require ungranted deployment permission.
targetScope = 'subscription'

resource lab 'Microsoft.Resources/resourceGroups@2024-03-01' existing = {
  name: 'rg-sentinelops-mxdr'
}

resource workspace 'Microsoft.OperationalInsights/workspaces@2025-02-01' existing = {
  name: 'law-sentinelops-mxdr-euw'
  scope: lab
}

resource sentinel 'Microsoft.SecurityInsights/onboardingStates@2024-03-01' existing = {
  name: 'default'
  scope: workspace
}

resource activityExport 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' existing = {
  name: 'subscriptionToLa'
}

resource machine 'Microsoft.HybridCompute/machines@2025-01-13' existing = {
  name: 'lab-sentinelops-linux-01'
  scope: lab
}

resource collection 'Microsoft.Insights/dataCollectionRules@2024-03-11' existing = {
  name: 'dcr-sentinelops-ama-linux'
  scope: lab
}

// These identifiers are private deployment outputs, never public evidence.
// Existing declarations and compilation do not independently prove existence.
output inventory object = {
  resourceGroup: lab.id
  workspace: workspace.id
  sentinel: sentinel.id
  activityExport: activityExport.id
  arcMachine: machine.id
  dcr: collection.id
}

output preserve object = {
  region: 'westeurope'
  pricing: 'pergb2018'
  retentionDays: 30
  dailyCapGb: json('0.1')
  source: 'local4 Warning and higher'
  deploymentsPermittedByThisFile: false
}
