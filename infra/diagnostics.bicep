// Phase after foundation: workspace exists, export is still OFF. No live KQL proof.
targetScope = 'resourceGroup'
@minLength(1)
param location string
@minLength(3)
@maxLength(16)
param prefix string
@minLength(1)
@maxLength(64)
param ownerTag string
@minLength(20)
@maxLength(20)
param expiresAt string
@description('False for C4. Enabling export requires separately authorized live table/transform/canary verification.')
param diagnosticExportEnabled bool = false

var tags = { project: 'morrow-supply', owner: ownerTag, stage: 'M4C-design', expiresAt: expiresAt }
var workspaceId = resourceId('Microsoft.OperationalInsights/workspaces', '${prefix}-logs')

resource transform 'Microsoft.Insights/dataCollectionRules@2023-03-11' = {
  name: '${prefix}-redaction'
  location: location
  tags: tags
  kind: 'WorkspaceTransforms'
  properties: {
    destinations: { logAnalytics: [{ name: 'safeLogs', workspaceResourceId: workspaceId }] }
    dataFlows: [
      {
        streams: ['Microsoft-Table-ContainerAppConsoleLogs']
        destinations: ['safeLogs']
        transformKql: trim(loadTextContent('diagnostics-console.kql'))
      }
      {
        streams: ['Microsoft-Table-ContainerAppSystemLogs']
        destinations: ['safeLogs']
        transformKql: trim(loadTextContent('diagnostics-system.kql'))
      }
    ]
  }
}

// Complete workspace update, NOT a property-only patch. Foundation must have run first.
// Literal workspaceId above deliberately prevents a dependency cycle with this update.
resource workspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: '${prefix}-logs'
  location: location
  tags: tags
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 30
    workspaceCapping: { dailyQuotaGb: json('0.1') }
    features: { disableLocalAuth: true, enableLogAccessUsingOnlyResourcePermissions: false }
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
    defaultDataCollectionRuleResourceId: transform.id
  }
}

resource environmentResource 'Microsoft.App/managedEnvironments@2025-07-01' existing = { name: '${prefix}-env' }
resource export 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = if (diagnosticExportEnabled) {
  name: 'sanitized-console-system-only'
  scope: environmentResource
  properties: {
    workspaceId: workspace.id
    logAnalyticsDestinationType: 'Dedicated'
    logs: [
      { category: 'ContainerAppConsoleLogs', enabled: true }
      { category: 'ContainerAppSystemLogs', enabled: true }
    ]
    metrics: []
  }
}
