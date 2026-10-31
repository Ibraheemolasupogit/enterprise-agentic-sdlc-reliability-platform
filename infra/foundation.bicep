targetScope = 'resourceGroup'

@description('Owner-approved region; no default or deployment authorization is supplied.')
param location string
@minLength(3)
@maxLength(20)
param prefix string
@minLength(5)
@maxLength(50)
param registryName string
@description('Pre-reviewed dedicated ACA infrastructure subnet; networking/private SQL is M4 work.')
param infrastructureSubnetId string
param ownerTag string

var tags = { project: 'morrow-supply', owner: ownerTag, stage: 'M4-candidate' }

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

resource environment 'Microsoft.App/managedEnvironments@2025-07-01' = {
  name: '${prefix}-env'
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: { destination: 'none' }
    vnetConfiguration: { infrastructureSubnetId: infrastructureSubnetId, internal: false }
    workloadProfiles: [{ name: 'Consumption', workloadProfileType: 'Consumption' }]
    peerAuthentication: { mtls: { enabled: true } }
  }
}

output registryId string = registry.id
output pullIdentityId string = pullIdentity.id
output apiIdentityId string = apiIdentity.id
output environmentId string = environment.id
