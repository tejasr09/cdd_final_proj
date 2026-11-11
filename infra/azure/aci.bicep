targetScope = 'resourceGroup'

@description('Human-selected Azure region. Keep ACI close to the PostgreSQL service where possible.')
param location string

@description('Name for the Linux container group.')
param containerGroupName string = 'ripple-effect-demo'

@description('Name of the existing Premium ACR created by provision.bicep.')
param registryName string

@description('Name of the existing user-assigned identity granted AcrPull on the registry.')
param imagePullIdentityName string = 'ripple-effect-aci-pull'

@description('Full ACR image reference pinned to a sha256 digest, not a mutable tag.')
param apiImage string

@description('Full ACR image reference pinned to a sha256 digest, not a mutable tag.')
param webImage string

@secure()
@description('Existing PostgreSQL SQLAlchemy URL. Must use TLS; never store it in source control.')
param databaseUrl string

@description('Public HTTP ingress is disabled by default. Do not enable until production auth and TLS ingress are approved.')
param publicIngressEnabled bool = false

@description('Globally unique ACI DNS label; required only when public ingress is explicitly enabled.')
param dnsNameLabel string = ''

@minLength(1)
@description('Human-selected owner/team tag; do not put personal contact details here.')
param owner string

@description('Deployment environment tag.')
param environment string = 'demo'

resource registry 'Microsoft.ContainerRegistry/registries@2025-11-01' existing = {
  name: registryName
}

resource imagePullIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' existing = {
  name: imagePullIdentityName
}

resource containerGroup 'Microsoft.ContainerInstance/containerGroups@2023-05-01' = {
  name: containerGroupName
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${imagePullIdentity.id}': {}
    }
  }
  properties: {
    containers: [
      {
        name: 'api'
        properties: {
          image: apiImage
          ports: [
            {
              port: 8000
              protocol: 'TCP'
            }
          ]
          environmentVariables: [
            {
              name: 'APP_ENV'
              value: 'production'
            }
            {
              name: 'ENABLE_LOCAL_AUTH'
              value: 'false'
            }
            {
              name: 'SEED_DEMO_DATA'
              value: 'false'
            }
            {
              name: 'DATABASE_URL'
              secureValue: databaseUrl
            }
          ]
          resources: {
            requests: {
              cpu: any('0.5')
              memoryInGB: any('1.5')
            }
          }
          livenessProbe: {
            httpGet: {
              path: '/api/v1/health/live'
              port: 8000
              scheme: 'Http'
            }
            initialDelaySeconds: 30
            periodSeconds: 30
            failureThreshold: 3
          }
          readinessProbe: {
            httpGet: {
              path: '/api/v1/health/ready'
              port: 8000
              scheme: 'Http'
            }
            initialDelaySeconds: 15
            periodSeconds: 10
            failureThreshold: 3
          }
        }
      }
      {
        name: 'web'
        properties: {
          image: webImage
          ports: [
            {
              port: 8080
              protocol: 'TCP'
            }
          ]
          environmentVariables: [
            {
              name: 'API_UPSTREAM'
              // ACI containers in one group share localhost: https://learn.microsoft.com/azure/container-instances/container-instances-multi-container-group
              value: '127.0.0.1:8000'
            }
          ]
          resources: {
            requests: {
              cpu: any('0.25')
              memoryInGB: any('0.5')
            }
          }
          livenessProbe: {
            httpGet: {
              path: '/health'
              port: 8080
              scheme: 'Http'
            }
            initialDelaySeconds: 10
            periodSeconds: 30
            failureThreshold: 3
          }
          readinessProbe: {
            httpGet: {
              path: '/health'
              port: 8080
              scheme: 'Http'
            }
            initialDelaySeconds: 5
            periodSeconds: 10
            failureThreshold: 3
          }
        }
      }
    ]
    imageRegistryCredentials: [
      {
        server: registry.properties.loginServer
        identity: imagePullIdentity.id
      }
    ]
    osType: 'Linux'
    restartPolicy: 'Always'
    ipAddress: publicIngressEnabled
      ? {
          type: 'Public'
          dnsNameLabel: dnsNameLabel
          ports: [
            {
              port: 8080
              protocol: 'TCP'
            }
          ]
        }
      : null
  }
  tags: {
    project: 'ripple-effect'
    environment: environment
    owner: owner
  }
}

output containerGroupId string = containerGroup.id
output publicIngressEnabled bool = publicIngressEnabled
