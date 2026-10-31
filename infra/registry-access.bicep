// Privileged bootstrap only: never run by the publisher or application release identity.
targetScope = 'resourceGroup'
param prefix string
param registryName string

resource registry 'Microsoft.ContainerRegistry/registries@2025-04-01' existing = { name: registryName }
resource pullIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2024-11-30' existing = { name: '${prefix}-pull' }

resource pullAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(registry.id, pullIdentity.id, 'AcrPull')
  scope: registry
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d')
    principalId: pullIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}
