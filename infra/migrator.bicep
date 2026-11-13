// Definition only. No execution/start/schedule, SQL principal or data grant is created.
targetScope = 'resourceGroup'
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
@minLength(3)
@maxLength(50)
param sqlServerName string
@minLength(1)
@maxLength(50)
param sqlDatabase string
@minLength(71)
@maxLength(71)
param apiDigest string
@allowed(['migrate', 'seed'])
param migrationOperation string

resource environmentResource 'Microsoft.App/managedEnvironments@2025-07-01' existing = { name: '${prefix}-env' }
resource registry 'Microsoft.ContainerRegistry/registries@2025-04-01' existing = { name: registryName }
resource pullIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2024-11-30' existing = {
  name: '${prefix}-pull'
}
resource apiIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2024-11-30' existing = {
  name: '${prefix}-api-runtime'
}
resource migratorIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2024-11-30' existing = {
  name: '${prefix}-migrator'
}

resource job 'Microsoft.App/jobs@2025-07-01' = {
  name: '${prefix}-migrator'
  location: location
  tags: { project: 'morrow-supply', owner: ownerTag, stage: 'M4C-design', expiresAt: expiresAt }
  identity: { type: 'UserAssigned', userAssignedIdentities: { '${pullIdentity.id}': {}, '${migratorIdentity.id}': {} } }
  properties: {
    environmentId: environmentResource.id
    workloadProfileName: 'Consumption'
    configuration: {
      triggerType: 'Manual'
      replicaTimeout: 600
      replicaRetryLimit: 0
      manualTriggerConfig: { parallelism: 1, replicaCompletionCount: 1 }
      identitySettings: [
        { identity: pullIdentity.id, lifecycle: 'None' }
        { identity: migratorIdentity.id, lifecycle: 'Main' }
      ]
      registries: [{ server: registry.properties.loginServer, identity: pullIdentity.id }]
      secrets: []
    }
    template: {
      containers: [
        {
          name: 'migrator'
          image: '${registry.properties.loginServer}/morrow-api@${apiDigest}'
          command: ['node']
          args: ['api/dist/sql-cli.js', migrationOperation, '--confirm-sql-change']
          resources: { cpu: json('0.25'), memory: '0.5Gi' }
          env: [
            { name: 'SQL_SERVER', value: '${sqlServerName}${environment().suffixes.sqlServerHostname}' }
            { name: 'SQL_DATABASE', value: sqlDatabase }
            { name: 'SQL_CLIENT_ID', value: apiIdentity.properties.clientId }
            { name: 'SQL_MIGRATOR_CLIENT_ID', value: migratorIdentity.properties.clientId }
          ]
        }
      ]
    }
  }
}
