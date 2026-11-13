// Bootstrap contract only. SQL users/grants and all live tests remain separately gated.
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
@minLength(3)
@maxLength(50)
param sqlServerName string
@minLength(1)
@maxLength(50)
param sqlDatabase string
@description('Existing owner-approved Entra admin GROUP, not an app/migrator identity. No group/user is created.')
@minLength(36)
@maxLength(36)
param sqlAdminGroupObjectId string
@minLength(1)
@maxLength(128)
param sqlAdminGroupName string

var tags = { project: 'morrow-supply', owner: ownerTag, stage: 'M4C-design', expiresAt: expiresAt }

resource server 'Microsoft.Sql/servers@2023-08-01' = {
  name: sqlServerName
  location: location
  tags: tags
  properties: {
    version: '12.0'
    publicNetworkAccess: 'Disabled'
    minimalTlsVersion: '1.2'
    restrictOutboundNetworkAccess: 'Enabled'
    administrators: {
      administratorType: 'ActiveDirectory'
      principalType: 'Group'
      login: sqlAdminGroupName
      sid: sqlAdminGroupObjectId
      tenantId: subscription().tenantId
      azureADOnlyAuthentication: true
    }
  }
}
resource connectionPolicy 'Microsoft.Sql/servers/connectionPolicies@2023-08-01' = {
  parent: server
  name: 'default'
  properties: { connectionType: 'Proxy' }
}
resource database 'Microsoft.Sql/servers/databases@2023-08-01' = {
  parent: server
  name: sqlDatabase
  location: location
  tags: tags
  sku: { name: 'Basic', tier: 'Basic', capacity: 5 }
  properties: {
    createMode: 'Default'
    maxSizeBytes: 2147483648
    collation: 'SQL_Latin1_General_CP1_CI_AS'
    requestedBackupStorageRedundancy: 'Local'
    zoneRedundant: false
    readScale: 'Disabled'
  }
}
resource encryption 'Microsoft.Sql/servers/databases/transparentDataEncryption@2023-08-01' = {
  parent: database
  name: 'current'
  properties: { state: 'Enabled' }
}
resource shortTermRetention 'Microsoft.Sql/servers/databases/backupShortTermRetentionPolicies@2023-08-01' = {
  parent: database
  name: 'default'
  properties: { retentionDays: 7 }
}
resource endpoint 'Microsoft.Network/privateEndpoints@2024-05-01' = {
  name: '${prefix}-sql-pe'
  location: location
  tags: tags
  properties: {
    subnet: { id: resourceId('Microsoft.Network/virtualNetworks/subnets', '${prefix}-vnet', 'private-endpoints') }
    privateLinkServiceConnections: [
      { name: 'sql', properties: { privateLinkServiceId: server.id, groupIds: ['sqlServer'] } }
    ]
  }
}
resource endpointDns 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2024-05-01' = {
  parent: endpoint
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'sql'
        properties: {
          privateDnsZoneId: resourceId(
            'Microsoft.Network/privateDnsZones',
            'privatelink${environment().suffixes.sqlServerHostname}'
          )
        }
      }
    ]
  }
}

output sqlServer string = '${server.name}${environment().suffixes.sqlServerHostname}'
output sqlDatabaseId string = database.id
