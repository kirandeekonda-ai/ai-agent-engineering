# Azure Deployment Guide for AI Agent Server

## 🎯 Goal
Deploy the Week 15 Agent Server to Azure Container Apps (serverless, scalable).

---

## 📋 Prerequisites

Before starting, ensure you have:

- [ ] Azure account (free tier works)
- [ ] Azure CLI installed (`az --version`)
- [ ] Docker Desktop installed
- [ ] Your `.env` file with `GROQ_API_KEY`

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Azure Architecture                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Internet → Azure Container Apps → Your Agent Server        │
│                     ↓                                        │
│              Auto-scaling (0 to N instances)                │
│                     ↓                                        │
│              Azure Container Registry (stores Docker image) │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📝 Step-by-Step Deployment

### Step 1: Install Azure CLI

```powershell
# Windows (using winget)
winget install Microsoft.AzureCLI

# Verify installation
az --version

# Login to Azure
az login
```

### Step 2: Create Azure Resources

```powershell
# Set variables
$RESOURCE_GROUP = "ai-agent-rg"
$LOCATION = "eastus"
$ACR_NAME = "aiagentacr$(Get-Random -Maximum 9999)"
$APP_NAME = "ai-agent-server"

# Create resource group
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create container registry
az acr create --resource-group $RESOURCE_GROUP --name $ACR_NAME --sku Basic

# Enable admin access
az acr update --name $ACR_NAME --admin-enabled true

# Get ACR credentials (save these!)
az acr credential show --name $ACR_NAME
```

### Step 3: Build and Push Docker Image

```powershell
# Navigate to Week 15
cd "Week 15 - Deployment"

# Login to ACR
az acr login --name $ACR_NAME

# Build and push image
docker build -t $ACR_NAME.azurecr.io/ai-agent:v1 .
docker push $ACR_NAME.azurecr.io/ai-agent:v1
```

### Step 4: Create Container App Environment

```powershell
# Install Container Apps extension
az extension add --name containerapp --upgrade

# Create environment
az containerapp env create `
  --name ai-agent-env `
  --resource-group $RESOURCE_GROUP `
  --location $LOCATION
```

### Step 5: Deploy Container App

```powershell
# Get ACR password
$ACR_PASSWORD = $(az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv)

# Deploy the app
az containerapp create `
  --name $APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --environment ai-agent-env `
  --image "$ACR_NAME.azurecr.io/ai-agent:v1" `
  --target-port 8000 `
  --ingress external `
  --registry-server "$ACR_NAME.azurecr.io" `
  --registry-username $ACR_NAME `
  --registry-password $ACR_PASSWORD `
  --secrets groq-key="YOUR_GROQ_API_KEY" `
  --env-vars GROQ_API_KEY=secretref:groq-key `
  --min-replicas 0 `
  --max-replicas 3 `
  --cpu 0.5 `
  --memory 1Gi
```

### Step 6: Get Your App URL

```powershell
# Get the app URL
az containerapp show `
  --name $APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --query properties.configuration.ingress.fqdn -o tsv
```

Your API is now live at: `https://<app-name>.<region>.azurecontainerapps.io`

---

## 🧪 Test Your Deployment

```powershell
# Replace with your actual URL
$APP_URL = "https://ai-agent-server.eastus.azurecontainerapps.io"

# Health check
Invoke-RestMethod -Uri "$APP_URL/health"

# Chat test
$body = @{
    message = "What is Python?"
} | ConvertTo-Json

Invoke-RestMethod -Uri "$APP_URL/chat" -Method Post -Body $body -ContentType "application/json"
```

---

## 💰 Cost Estimate

| Resource | Free Tier | Pay-as-you-go |
|----------|-----------|---------------|
| Container Apps | 180K vCPU-seconds/month | ~$0.000024/vCPU-second |
| Container Registry | N/A | ~$5/month (Basic) |
| **Total (light use)** | **$0** | **~$10/month** |

---

## 🔧 Updating Your App

```powershell
# Build new version
docker build -t $ACR_NAME.azurecr.io/ai-agent:v2 .
docker push $ACR_NAME.azurecr.io/ai-agent:v2

# Update container app
az containerapp update `
  --name $APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --image "$ACR_NAME.azurecr.io/ai-agent:v2"
```

---

## 🧹 Cleanup (When Done)

```powershell
# Delete everything to stop charges
az group delete --name $RESOURCE_GROUP --yes --no-wait
```

---

## ✅ Deployment Checklist

- [ ] Azure CLI installed and logged in
- [ ] Resource group created
- [ ] Container Registry created
- [ ] Docker image built and pushed
- [ ] Container App environment created
- [ ] Container App deployed with secrets
- [ ] Health check passing
- [ ] Chat endpoint working

---

## 🚨 Troubleshooting

| Issue | Solution |
|-------|----------|
| Docker build fails | Check Dockerfile syntax, ensure requirements.txt exists |
| Push to ACR fails | Run `az acr login --name <acr-name>` |
| App not starting | Check logs: `az containerapp logs show --name <app> --resource-group <rg>` |
| 500 errors | Verify GROQ_API_KEY secret is set correctly |
