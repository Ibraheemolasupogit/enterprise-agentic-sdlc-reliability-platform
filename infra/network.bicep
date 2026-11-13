// Original C4 definitions; no address allocation or deployment is authorized.
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
@description('Reviewed RFC1918 network; offline preflight checks containment, alignment and overlap.')
param vnetCidr string
@description('Dedicated Microsoft.App/environments subnet, /27 or larger; never share with endpoints.')
param acaSubnetCidr string
param privateEndpointSubnetCidr string

var tags = { project: 'morrow-supply', owner: ownerTag, stage: 'M4C-design', expiresAt: expiresAt }

resource acaNsg 'Microsoft.Network/networkSecurityGroups@2024-05-01' = {
  name: '${prefix}-aca-nsg'
  location: location
  tags: tags
  properties: {
    securityRules: [
      {
        name: 'IntraSubnetIn'
        properties: {
          priority: 100
          direction: 'Inbound'
          access: 'Allow'
          protocol: '*'
          sourcePortRange: '*'
          destinationPortRange: '*'
          sourceAddressPrefix: acaSubnetCidr
          destinationAddressPrefix: acaSubnetCidr
        }
      }
      {
        name: 'LoadBalancerProbes'
        properties: {
          priority: 110
          direction: 'Inbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRange: '30000-32767'
          sourceAddressPrefix: 'AzureLoadBalancer'
          destinationAddressPrefix: acaSubnetCidr
        }
      }
      {
        name: 'DenyOtherIn'
        properties: {
          priority: 4096
          direction: 'Inbound'
          access: 'Deny'
          protocol: '*'
          sourcePortRange: '*'
          destinationPortRange: '*'
          sourceAddressPrefix: '*'
          destinationAddressPrefix: '*'
        }
      }
      {
        name: 'IntraSubnetOut'
        properties: {
          priority: 100
          direction: 'Outbound'
          access: 'Allow'
          protocol: '*'
          sourcePortRange: '*'
          destinationPortRange: '*'
          sourceAddressPrefix: acaSubnetCidr
          destinationAddressPrefix: acaSubnetCidr
        }
      }
      {
        name: 'PrivateSqlProxy'
        properties: {
          priority: 110
          direction: 'Outbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRange: '1433'
          sourceAddressPrefix: acaSubnetCidr
          destinationAddressPrefix: privateEndpointSubnetCidr
        }
      }
      {
        name: 'AzureDns'
        properties: {
          priority: 120
          direction: 'Outbound'
          access: 'Allow'
          protocol: '*'
          sourcePortRange: '*'
          destinationPortRange: '53'
          sourceAddressPrefix: acaSubnetCidr
          destinationAddressPrefix: 'AzurePlatformDNS'
        }
      }
      // Public ACR/IdP/platform HTTPS. This is a port bound, NOT an FQDN egress firewall.
      {
        name: 'RequiredPublicHttps'
        properties: {
          priority: 130
          direction: 'Outbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRange: '443'
          sourceAddressPrefix: acaSubnetCidr
          destinationAddressPrefix: 'Internet'
        }
      }
      {
        name: 'DenyOtherOut'
        properties: {
          priority: 4096
          direction: 'Outbound'
          access: 'Deny'
          protocol: '*'
          sourcePortRange: '*'
          destinationPortRange: '*'
          sourceAddressPrefix: '*'
          destinationAddressPrefix: '*'
        }
      }
    ]
  }
}

resource endpointNsg 'Microsoft.Network/networkSecurityGroups@2024-05-01' = {
  name: '${prefix}-endpoint-nsg'
  location: location
  tags: tags
  properties: {
    securityRules: [
      {
        name: 'AcaSqlProxy'
        properties: {
          priority: 100
          direction: 'Inbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRange: '1433'
          sourceAddressPrefix: acaSubnetCidr
          destinationAddressPrefix: privateEndpointSubnetCidr
        }
      }
      {
        name: 'DenyOtherIn'
        properties: {
          priority: 4096
          direction: 'Inbound'
          access: 'Deny'
          protocol: '*'
          sourcePortRange: '*'
          destinationPortRange: '*'
          sourceAddressPrefix: '*'
          destinationAddressPrefix: '*'
        }
      }
      {
        name: 'DenyOtherOut'
        properties: {
          priority: 4096
          direction: 'Outbound'
          access: 'Deny'
          protocol: '*'
          sourcePortRange: '*'
          destinationPortRange: '*'
          sourceAddressPrefix: '*'
          destinationAddressPrefix: '*'
        }
      }
    ]
  }
}

resource vnet 'Microsoft.Network/virtualNetworks@2024-05-01' = {
  name: '${prefix}-vnet'
  location: location
  tags: tags
  properties: {
    addressSpace: { addressPrefixes: [vnetCidr] }
    // Azure-provided DNS and system routes; no unapproved paid resolver/NAT/UDR.
    dhcpOptions: { dnsServers: [] }
    subnets: [
      {
        name: 'aca'
        properties: {
          addressPrefix: acaSubnetCidr
          delegations: [{ name: 'aca', properties: { serviceName: 'Microsoft.App/environments' } }]
          networkSecurityGroup: { id: acaNsg.id }
          privateEndpointNetworkPolicies: 'Enabled'
          serviceEndpoints: []
        }
      }
      {
        name: 'private-endpoints'
        properties: {
          addressPrefix: privateEndpointSubnetCidr
          delegations: []
          networkSecurityGroup: { id: endpointNsg.id }
          privateEndpointNetworkPolicies: 'Enabled'
          serviceEndpoints: []
        }
      }
    ]
  }
}

resource sqlDns 'Microsoft.Network/privateDnsZones@2024-06-01' = {
  name: 'privatelink${environment().suffixes.sqlServerHostname}'
  location: 'global'
  tags: tags
}
resource dnsLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2024-06-01' = {
  parent: sqlDns
  name: '${prefix}-sql-link'
  location: 'global'
  tags: tags
  properties: { registrationEnabled: false, virtualNetwork: { id: vnet.id } }
}

output infrastructureSubnetId string = resourceId('Microsoft.Network/virtualNetworks/subnets', vnet.name, 'aca')
output privateEndpointSubnetId string = resourceId(
  'Microsoft.Network/virtualNetworks/subnets',
  vnet.name,
  'private-endpoints'
)
output sqlPrivateDnsZoneId string = sqlDns.id
