// Validation-only M3 skeleton. Never deploy the unauthenticated SQLite M2 images.
targetScope = 'resourceGroup'
param location string
param prefix string
param registryName string
param ownerTag string
@description('Approved M4-ready image SHA-256, including sha256: prefix; no tag/latest accepted.')
@minLength(71)
@maxLength(71)
param apiDigest string
@minLength(71)
@maxLength(71)
param frontendDigest string

resource environment 'Microsoft.App/managedEnvironments@2025-07-01' existing = { name: '${prefix}-env' }
resource registry 'Microsoft.ContainerRegistry/registries@2025-04-01' existing = { name: registryName }
resource pullIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2024-11-30' existing = { name: '${prefix}-pull' }
resource apiIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2024-11-30' existing = { name: '${prefix}-api-runtime' }

var tags = { project: 'morrow-supply', owner: ownerTag, stage: 'M4-candidate' }
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
      identitySettings: pullSettings
      registries: registries
      ingress: { external: false, targetPort: 3000, transport: 'http', allowInsecure: false }
    }
    template: {
      containers: [{
        name: 'api'
        image: '${registry.properties.loginServer}/morrow-api@${apiDigest}'
        resources: { cpu: json('0.25'), memory: '0.5Gi' }
        probes: [
          { type: 'Liveness', httpGet: { path: '/health/live', port: 3000 }, initialDelaySeconds: 5, periodSeconds: 10 }
          { type: 'Readiness', httpGet: { path: '/health/ready', port: 3000 }, periodSeconds: 5, timeoutSeconds: 2 }
        ]
      }]
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
      ingress: { external: true, targetPort: 8080, transport: 'http', allowInsecure: false }
    }
    template: {
      containers: [{
        name: 'frontend'
        image: '${registry.properties.loginServer}/morrow-frontend@${frontendDigest}'
        env: [{ name: 'API_ORIGIN', value: 'https://${api.properties.configuration.ingress.fqdn}' }]
        resources: { cpu: json('0.25'), memory: '0.5Gi' }
        probes: [
          { type: 'Liveness', httpGet: { path: '/health/live', port: 8080 }, initialDelaySeconds: 5, periodSeconds: 10 }
          { type: 'Readiness', httpGet: { path: '/health/ready', port: 8080 }, periodSeconds: 5, timeoutSeconds: 3 }
        ]
      }]
      scale: { minReplicas: 0, maxReplicas: 1 }
    }
  }
}
