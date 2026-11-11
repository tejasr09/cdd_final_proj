targetScope = 'resourceGroup'

@description('Human-selected Azure region. Confirm eligibility and cost before deployment.')
param location string

@minLength(5)
@maxLength(50)
@description('Globally unique lowercase alphanumeric ACR name.')
param registryName string

@description('User-assigned identity used by ACI to pull private images.')
param imagePullIdentityName string = 'ripple-effect-aci-pull'

@minLength(1)
@description('Human-selected owner/team tag; do not put personal contact details here.')
param owner string

@description('Deployment environment tag.')
param environment string = 'demo'

var acrPullRoleDefinitionId = '7f951dda-4ed3-4680-a7ca-43fe172d538d'

resource registry 'Microsoft.ContainerRegistry/registries@2025-11-01' = {
  name: registryName
  location: location
  sku: {
    // ACI managed-identity pulls require Premium ACR: https://learn.microsoft.com/azure/container-instances/using-azure-container-registry-mi
    name: 'Premium'
  }
  properties: {
    adminUserEnabled: false
    anonymousPullEnabled: false
    publicNetworkAccess: 'Enabled'
  }
  tags: {
    project: 'ripple-effect'
    environment: environment
    owner: owner
  }
}

resource imagePullIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: imagePullIdentityName
  location: location
  tags: {
    project: 'ripple-effect'
    environment: environment
    owner: owner
  }
}

resource acrPullAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: registry
  name: guid(registry.id, imagePullIdentity.id, acrPullRoleDefinitionId)
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      acrPullRoleDefinitionId
    )
    principalId: imagePullIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

output registryId string = registry.id
output registryLoginServer string = registry.properties.loginServer
output imagePullIdentityId string = imagePullIdentity.id
