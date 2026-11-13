// C4 static candidate; real provider/private SQL/identity/governance remain NO-GO.
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
@minLength(40)
@maxLength(40)
param releaseSha string
@minLength(64)
@maxLength(64)
param configSha256 string
@minValue(1)
@maxValue(1)
@allowed([1])
@description('Current pinned SQL migration contract is version 1; a new migration requires reviewed definition changes.')
param schemaVersion int
@minLength(1)
param publicOrigin string
@description('One owner-reviewed public client IPv4 CIDR, /24 or narrower; no world-open rehearsal.')
@minLength(9)
@maxLength(18)
param frontendClientCidr string
@minLength(1)
param oidcIssuer string
@minLength(1)
param oidcJwksUri string
@minLength(1)
param oidcAudience string
@minLength(1)
param oidcRequiredRole string
@minLength(1)
param oidcRequiredScope string
@minLength(1)
param oidcSpaClientId string
@minLength(1)
param oidcSpaScopes string
@minLength(1)
param oidcConnectOrigin string
@description('Reviewed resolver IP for the selected ACA network; never assume Docker DNS in Azure.')
@minLength(1)
param dnsResolver string
@minLength(1)
@maxLength(50)
param sqlServerName string
@minLength(1)
param sqlDatabase string
@description('Approved M4-ready image SHA-256, including sha256: prefix; no tag/latest accepted.')
@minLength(71)
@maxLength(71)
param apiDigest string
@minLength(71)
@maxLength(71)
param frontendDigest string

resource environment 'Microsoft.App/managedEnvironments@2025-07-01' existing = { name: '${prefix}-env' }
resource registry 'Microsoft.ContainerRegistry/registries@2025-04-01' existing = { name: registryName }
resource pullIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2024-11-30' existing = {
  name: '${prefix}-pull'
}
resource apiIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2024-11-30' existing = {
  name: '${prefix}-api-runtime'
}

var tags = {
  project: 'morrow-supply'
  owner: ownerTag
  stage: 'M4C-design'
  expiresAt: expiresAt
  releaseSha: releaseSha
  configSha256: configSha256
  schemaVersion: string(schemaVersion)
}
var revisionSuffix = 'r${substring(releaseSha, 0, 12)}-c${substring(configSha256, 0, 12)}-s${schemaVersion}'
var pullSettings = [{ identity: pullIdentity.id, lifecycle: 'None' }]
var registries = [{ server: registry.properties.loginServer, identity: pullIdentity.id }]

resource api 'Microsoft.App/containerApps@2025-07-01' = {
  name: '${prefix}-api'
  location: location
  tags: tags
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: { '${pullIdentity.id}': {}, '${apiIdentity.id}': {} }
  }
  properties: {
    managedEnvironmentId: environment.id
    workloadProfileName: 'Consumption'
    configuration: {
      activeRevisionsMode: 'Single'
      identitySettings: [
        { identity: pullIdentity.id, lifecycle: 'None' }
        { identity: apiIdentity.id, lifecycle: 'Main' }
      ]
      registries: registries
      secrets: []
      ingress: { external: false, targetPort: 3000, transport: 'http', allowInsecure: false }
    }
    template: {
      revisionSuffix: revisionSuffix
      containers: [
        {
          name: 'api'
          image: '${registry.properties.loginServer}/morrow-api@${apiDigest}'
          env: [
            { name: 'APP_ENV', value: 'cloud' }
            { name: 'AUTH_MODE', value: 'oidc' }
            { name: 'DATABASE_BACKEND', value: 'sql' }
            { name: 'ALLOWED_ORIGINS', value: publicOrigin }
            { name: 'OIDC_ISSUER', value: oidcIssuer }
            { name: 'OIDC_JWKS_URI', value: oidcJwksUri }
            { name: 'OIDC_AUDIENCE', value: oidcAudience }
            { name: 'OIDC_REQUIRED_ROLE', value: oidcRequiredRole }
            { name: 'OIDC_REQUIRED_SCOPE', value: oidcRequiredScope }
            { name: 'SQL_SERVER', value: '${sqlServerName}${az.environment().suffixes.sqlServerHostname}' }
            { name: 'SQL_DATABASE', value: sqlDatabase }
            { name: 'SQL_CLIENT_ID', value: apiIdentity.properties.clientId }
            { name: 'RELEASE_SHA', value: releaseSha }
            { name: 'CONFIG_SHA256', value: configSha256 }
            { name: 'SCHEMA_VERSION', value: string(schemaVersion) }
          ]
          resources: { cpu: json('0.25'), memory: '0.5Gi' }
          probes: [
            {
              type: 'Liveness'
              httpGet: { path: '/health/live', port: 3000 }
              initialDelaySeconds: 5
              periodSeconds: 10
            }
            { type: 'Readiness', httpGet: { path: '/health/ready', port: 3000 }, periodSeconds: 5, timeoutSeconds: 2 }
          ]
        }
      ]
      scale: { minReplicas: 0, maxReplicas: 1 }
    }
  }
}

resource frontend 'Microsoft.App/containerApps@2025-07-01' = {
  name: '${prefix}-frontend'
  location: location
  tags: tags
  identity: { type: 'UserAssigned', userAssignedIdentities: { '${pullIdentity.id}': {} } }
  properties: {
    managedEnvironmentId: environment.id
    workloadProfileName: 'Consumption'
    configuration: {
      activeRevisionsMode: 'Single'
      identitySettings: pullSettings
      registries: registries
      secrets: []
      ingress: {
        external: true
        targetPort: 8080
        transport: 'http'
        allowInsecure: false
        ipSecurityRestrictions: [{ name: 'approved-client', action: 'Allow', ipAddressRange: frontendClientCidr }]
      }
    }
    template: {
      revisionSuffix: revisionSuffix
      containers: [
        {
          name: 'frontend'
          image: '${registry.properties.loginServer}/morrow-frontend@${frontendDigest}'
          env: [
            { name: 'AUTH_MODE', value: 'oidc' }
            { name: 'PROXY_MODE', value: 'https' }
            { name: 'API_ORIGIN', value: 'https://${api.properties.configuration.ingress.fqdn}' }
            { name: 'TRUSTED_API_HOST', value: api.properties.configuration.ingress.fqdn }
            { name: 'DNS_RESOLVER', value: dnsResolver }
            { name: 'OIDC_ISSUER', value: oidcIssuer }
            { name: 'OIDC_CLIENT_ID', value: oidcSpaClientId }
            { name: 'OIDC_SCOPES', value: oidcSpaScopes }
            { name: 'OIDC_CONNECT_ORIGIN', value: oidcConnectOrigin }
            { name: 'PUBLIC_ORIGIN', value: publicOrigin }
          ]
          resources: { cpu: json('0.25'), memory: '0.5Gi' }
          probes: [
            {
              type: 'Liveness'
              httpGet: { path: '/health/live', port: 8080 }
              initialDelaySeconds: 5
              periodSeconds: 10
            }
            { type: 'Readiness', httpGet: { path: '/health/ready', port: 8080 }, periodSeconds: 5, timeoutSeconds: 3 }
          ]
        }
      ]
      scale: { minReplicas: 0, maxReplicas: 1 }
    }
  }
}
