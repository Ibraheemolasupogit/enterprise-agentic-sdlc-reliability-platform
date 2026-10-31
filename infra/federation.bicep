// Separately authorized identity administrator, not CI/release. No RBAC grants here.
targetScope = 'resourceGroup'
@description('Existing dedicated publisher OR release managed identity; apply separately per protected environment.')
param identityName string
@description('Exact reviewed emitted sub, including immutable IDs when applicable. No guessed name-only subject.')
@minLength(10)
param verifiedSubject string
@description('Name for this one exact federation binding, not a wildcard trust.')
param credentialName string

resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2024-11-30' existing = { name: identityName }
resource federation 'Microsoft.ManagedIdentity/userAssignedIdentities/federatedIdentityCredentials@2024-11-30' = {
  parent: identity
  name: credentialName
  properties: {
    issuer: 'https://token.actions.githubusercontent.com'
    audiences: ['api://AzureADTokenExchange']
    subject: verifiedSubject
  }
}
