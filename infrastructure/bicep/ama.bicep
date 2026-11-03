// Recovery representation only. No workflow deploys this template.
// Scope and every writable property match ama.cloud.contract().
targetScope = 'resourceGroup'

resource workspace 'Microsoft.OperationalInsights/workspaces@2025-02-01' existing = {
  name: 'law-sentinelops-mxdr-euw'
}

resource machine 'Microsoft.HybridCompute/machines@2025-01-13' existing = {
  name: 'lab-sentinelops-linux-01'
}

var ownership = {
  'sentinelops-source': 'ama-linux-syslog'
  'deployment-owner': 'github-oidc'
}

resource collection 'Microsoft.Insights/dataCollectionRules@2024-03-11' = {
  name: 'dcr-sentinelops-ama-linux'
  location: 'westeurope'
  kind: 'Linux'
  tags: ownership
  properties: {
    dataSources: {
      syslog: [
        {
          name: 'lab-local4-warning'
          streams: ['Microsoft-Syslog']
          facilityNames: ['local4']
          logLevels: ['Warning', 'Error', 'Critical', 'Alert', 'Emergency']
        }
      ]
    }
    destinations: {
      logAnalytics: [
        {
          name: 'existing-workspace'
          workspaceResourceId: workspace.id
        }
      ]
    }
    dataFlows: [
      {
        streams: ['Microsoft-Syslog']
        destinations: ['existing-workspace']
        transformKql: 'source'
        outputStream: 'Microsoft-Syslog'
      }
    ]
  }
}

resource agent 'Microsoft.HybridCompute/machines/extensions@2025-01-13' = {
  parent: machine
  name: 'AzureMonitorLinuxAgent'
  location: 'westeurope'
  tags: ownership
  properties: {
    publisher: 'Microsoft.Azure.Monitor'
    type: 'AzureMonitorLinuxAgent'
    typeHandlerVersion: '1.0'
    autoUpgradeMinorVersion: true
    enableAutomaticUpgrade: false
    settings: {}
  }
}

resource binding 'Microsoft.Insights/dataCollectionRuleAssociations@2024-03-11' = {
  name: 'sentinelops-ama-linux'
  scope: machine
  properties: {
    dataCollectionRuleId: collection.id
    description: 'Single owned local machine; local4 warning pilot only'
  }
}
