# ALIS Deployment Guide - Azure with GitHub Actions

This guide walks you through deploying the ALIS application to Azure using GitHub Actions for automated CI/CD.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         Azure Cloud                          │
│                                                               │
│  ┌──────────────────┐         ┌─────────────────────────┐   │
│  │  Static Web App  │────────▶│   App Service (Backend) │   │
│  │   (Frontend)     │  HTTPS  │      Python 3.11        │   │
│  │   Free Tier      │         │      F1 Free Tier       │   │
│  └──────────────────┘         └───────────┬─────────────┘   │
│                                            │                  │
│                                            │ Managed Identity │
│                                            ▼                  │
│                                ┌───────────────────────┐     │
│                                │     Key Vault         │     │
│                                │  - GEMINI_API_KEY     │     │
│                                │  - MONGO_URI          │     │
│                                └───────────────────────┘     │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                        ┌───────────────────────┐
                        │   MongoDB Atlas       │
                        │   (External)          │
                        └───────────────────────┘
```

## Prerequisites

1. **Azure CLI** installed and logged in
   ```bash
   az --version
   az login
   ```

2. **GitHub Repository** with your code
   - Repository: `https://github.com/TorstenS1/learning`
   - Ensure you have admin access

3. **Secrets Ready**
   - Gemini API Key: `the_key`
   - MongoDB URI: `mongodb+srv://alis_app_user:<alis_app_password>@cluster0.n5e9osz.mongodb.net/?appName=Cluster0`

## Step-by-Step Deployment

### Phase 1: Infrastructure Setup

#### 1.1 Run Infrastructure Setup Script

```bash
cd /home/torsten/dev/my-projects/learning
chmod +x setup_infrastructure.sh
./setup_infrastructure.sh
```

This script will:
- Create Resource Group `rg-alis-learning`
- Create Key Vault and store secrets
- Create App Service Plan (F1 Free)
- Create Web App for backend
- Configure Managed Identity and Key Vault access

**Expected Output:**
```
✅ Infrastructure Setup Complete!
Backend URL: https://app-alis-backend-XXXXX.azurewebsites.net
```

**Save the `UNIQUE_ID` (XXXXX) - you'll need it for GitHub secrets!**

#### 1.2 Get Azure Publish Profile

```bash
# Replace XXXXX with your UNIQUE_ID from step 1.1
BACKEND_APP_NAME="app-alis-backend-XXXXX"

az webapp deployment list-publishing-profiles \
  --name "${BACKEND_APP_NAME}" \
  --resource-group "rg-alis-learning" \
  --xml > publish-profile.xml

cat publish-profile.xml
```

Copy the entire XML content - you'll add it to GitHub secrets.

---

### Phase 2: Create Azure Static Web App

#### 2.1 Create Static Web App

```bash
# This will create the Static Web App and output the deployment token
az staticwebapp create \
  --name "stapp-alis-learning" \
  --resource-group "rg-alis-learning" \
  --location "westeurope" \
  --sku Free \
  --source "https://github.com/TorstenS1/learning" \
  --branch "main" \
  --app-location "frontend" \
  --output-location "dist" \
  --login-with-github
```

#### 2.2 Get Static Web App Deployment Token

```bash
az staticwebapp secrets list \
  --name "stapp-alis-learning" \
  --resource-group "rg-alis-learning" \
  --query "properties.apiKey" \
  --output tsv
```

Copy this token - you'll add it to GitHub secrets.

---

### Phase 3: Configure GitHub Secrets

Go to your GitHub repository: `https://github.com/TorstenS1/learning/settings/secrets/actions`

Add the following secrets:

| Secret Name | Value | Where to get it |
|-------------|-------|-----------------|
| `UNIQUE_ID` | `XXXXX` | From step 1.1 output |
| `AZURE_WEBAPP_PUBLISH_PROFILE` | XML content | From step 1.2 |
| `AZURE_STATIC_WEB_APPS_API_TOKEN` | Token string | From step 2.2 |

**Steps to add secrets:**
1. Click "New repository secret"
2. Enter the name exactly as shown above
3. Paste the value
4. Click "Add secret"

---

### Phase 4: Deploy

#### 4.1 Commit and Push Deployment Files

```bash
cd /home/torsten/dev/my-projects/learning

# Add all deployment files
git add .github/workflows/
git add setup_infrastructure.sh
git add startup.sh
git add requirements.txt
git add frontend/staticwebapp.config.json
git add DEPLOYMENT.md

# Commit
git commit -m "Add Azure deployment configuration"

# Push to trigger deployment
git push origin main
```

#### 4.2 Monitor Deployment

1. **Watch GitHub Actions:**
   - Go to: `https://github.com/TorstenS1/learning/actions`
   - You should see two workflows running:
     - "Deploy Backend to Azure App Service"
     - "Deploy Frontend to Azure Static Web Apps"

2. **Check Backend Deployment:**
   ```bash
   # Replace XXXXX with your UNIQUE_ID
   curl https://app-alis-backend-XXXXX.azurewebsites.net/api/health
   ```
   
   Expected response:
   ```json
   {
     "status": "healthy",
     "service": "ALIS Backend",
     "version": "1.0.0",
     "simulation_mode": false
   }
   ```

3. **Check Frontend Deployment:**
   - Get the Static Web App URL:
     ```bash
     az staticwebapp show \
       --name "stapp-alis-learning" \
       --resource-group "rg-alis-learning" \
       --query "defaultHostname" \
       --output tsv
     ```
   - Visit the URL in your browser

---

## Environment Variables Reference

### Backend (App Service)

Configured automatically by `setup_infrastructure.sh`:

| Variable | Source | Description |
|----------|--------|-------------|
| `GEMINI_API_KEY` | Key Vault | Gemini API key for LLM calls |
| `MONGODB_URI` | Key Vault | MongoDB connection string |
| `USE_LLM_SIMULATION` | Direct | Set to `false` for production |
| `DEBUG` | Direct | Set to `false` for production |
| `PORT` | Direct | `8000` |
| `CORS_ORIGINS` | Direct | `https://*.azurestaticapps.net` |

### Frontend (Static Web App)

Configured in GitHub Actions workflow:

| Variable | Value | Description |
|----------|-------|-------------|
| `VITE_API_URL` | `https://app-alis-backend-XXXXX.azurewebsites.net/api` | Backend API URL |

---

## Troubleshooting

### Backend Issues

#### 1. Health check fails
```bash
# Check app logs
az webapp log tail \
  --name "app-alis-backend-XXXXX" \
  --resource-group "rg-alis-learning"
```

#### 2. Key Vault access denied
```bash
# Verify managed identity has access
az keyvault show \
  --name "kv-alis-XXXXX" \
  --query "properties.accessPolicies" \
  --output table
```

#### 3. App won't start
- Check `startup.sh` is executable
- Verify `requirements.txt` includes `gunicorn`
- Check Python version is 3.11

### Frontend Issues

#### 1. Build fails
- Check `package.json` and `package-lock.json` are committed
- Verify Node version in workflow matches local (18.x)

#### 2. API calls fail (CORS)
- Verify `CORS_ORIGINS` in backend includes Static Web App domain
- Check browser console for specific CORS errors

#### 3. Routes return 404
- Verify `staticwebapp.config.json` is in `frontend/` directory
- Check `navigationFallback` configuration

### GitHub Actions Issues

#### 1. Workflow doesn't trigger
- Verify workflows are in `.github/workflows/`
- Check file paths in `on.push.paths` match your changes
- Ensure you pushed to `main` branch

#### 2. Secrets not found
- Verify secret names match exactly (case-sensitive)
- Check secrets are set at repository level, not environment level

---

## Updating the Application

### Backend Updates
1. Make changes to `backend/` or `requirements.txt`
2. Commit and push to `main`
3. GitHub Actions will automatically deploy

### Frontend Updates
1. Make changes to `frontend/`
2. Commit and push to `main`
3. GitHub Actions will automatically deploy

---

## Cost Monitoring

All services used are on free tiers, but monitor usage:

```bash
# Check resource costs
az consumption usage list \
  --start-date "2025-12-01" \
  --end-date "2025-12-31" \
  --output table
```

**Expected costs:**
- App Service (F1): **Free** (60 CPU min/day limit)
- Static Web Apps: **Free** (100 GB bandwidth/month)
- Key Vault: **~$0.03/month** (for secret operations)

---

## Cleanup / Teardown

To delete all resources:

```bash
az group delete \
  --name "rg-alis-learning" \
  --yes \
  --no-wait
```

This will delete:
- App Service Plan
- Web App
- Key Vault
- Static Web App
- All associated resources

---

## URLs Quick Reference

After deployment, save these URLs:

- **Frontend:** `https://stapp-alis-learning.azurestaticapps.net`
- **Backend:** `https://app-alis-backend-XXXXX.azurewebsites.net`
- **Health Check:** `https://app-alis-backend-XXXXX.azurewebsites.net/api/health`
- **Azure Portal:** `https://portal.azure.com/#@/resource/subscriptions/.../resourceGroups/rg-alis-learning`

---

## Support

For issues:
1. Check GitHub Actions logs
2. Check Azure App Service logs: `az webapp log tail`
3. Verify all secrets are correctly set
4. Ensure MongoDB Atlas allows Azure IPs
