targetScope = 'resourceGroup'

@description('Owner-approved region; no default or deployment authorization is supplied.')
@minLength(1)
param location string
@minLength(3)
@maxLength(16)
param prefix string
@minLength(5)
@maxLength(50)
param registryName string
@minLength(1)
@maxLength(64)
param ownerTag string
@minLength(20)
@maxLength(20)
param expiresAt string

var tags = { project: 'morrow-supply', owner: ownerTag, stage: 'M4C-design', expiresAt: expiresAt }

resource vnet 'Microsoft.Network/virtualNetworks@2024-05-01' existing = { name: '${prefix}-vnet' }

resource registry 'Microsoft.ContainerRegistry/registries@2025-04-01' = {
  name: registryName
  location: location
  tags: tags
  sku: { name: 'Basic' }
  properties: {
    adminUserEnabled: false
    anonymousPullEnabled: false
    publicNetworkAccess: 'Enabled'
    policies: { azureADAuthenticationAsArmPolicy: { status: 'enabled' } }
  }
}

resource pullIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2024-11-30' = {
  name: '${prefix}-pull'
  location: location
  tags: tags
}

resource apiIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2024-11-30' = {
  name: '${prefix}-api-runtime'
  location: location
  tags: tags
}

resource migratorIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2024-11-30' = {
  name: '${prefix}-migrator'
  location: location
  tags: tags
}
resource publisherIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2024-11-30' = {
  name: '${prefix}-publisher'
  location: location
  tags: tags
}
resource releaseIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2024-11-30' = {
  name: '${prefix}-release'
  location: location
  tags: tags
}

// Bootstrap workspace first; diagnostics.bicep later links the workspace transform.
// No diagnostic export is configured here, so no raw console/system log is retained.
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
  }
}

resource consoleTable 'Microsoft.OperationalInsights/workspaces/tables@2023-09-01' = {
  parent: workspace
  name: 'ContainerAppConsoleLogs'
  properties: {
    schema: { name: 'ContainerAppConsoleLogs' }
    plan: 'Analytics'
    retentionInDays: 30
    totalRetentionInDays: 30
  }
}
resource systemTable 'Microsoft.OperationalInsights/workspaces/tables@2023-09-01' = {
  parent: workspace
  name: 'ContainerAppSystemLogs'
  properties: {
    schema: { name: 'ContainerAppSystemLogs' }
    plan: 'Analytics'
    retentionInDays: 30
    totalRetentionInDays: 30
  }
}

resource environment 'Microsoft.App/managedEnvironments@2025-07-01' = {
  name: '${prefix}-env'
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: { destination: 'azure-monitor' }
    vnetConfiguration: {
      infrastructureSubnetId: resourceId('Microsoft.Network/virtualNetworks/subnets', vnet.name, 'aca')
      internal: false
    }
    workloadProfiles: [{ name: 'Consumption', workloadProfileType: 'Consumption' }]
    peerAuthentication: { mtls: { enabled: true } }
  }
}

output registryId string = registry.id
output pullIdentityId string = pullIdentity.id
output apiIdentityId string = apiIdentity.id
output migratorIdentityId string = migratorIdentity.id
output publisherIdentityId string = publisherIdentity.id
output releaseIdentityId string = releaseIdentity.id
output environmentId string = environment.id
output workspaceId string = workspace.id
