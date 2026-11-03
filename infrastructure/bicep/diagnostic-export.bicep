// Read-only representation: collection changes remain outside deployment scope.
targetScope = 'subscription'

resource workspace 'Microsoft.OperationalInsights/workspaces@2025-02-01' existing = {
  name: 'law-sentinelops-mxdr-euw'
  scope: resourceGroup('rg-sentinelops-mxdr')
}

resource export 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' existing = {
  name: 'subscriptionToLa'
}

// The destination is represented without assuming every Activity category.
// A real read-back must compare logs/categories before changing this export.
output expectedDestination string = workspace.id
output existingExport string = export.id
