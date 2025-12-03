#!/bin/bash
set -e

echo "=========================================="
echo "ALIS Azure Infrastructure Setup"
echo "=========================================="

# Configuration
RESOURCE_GROUP="rg-alis-learning"
LOCATION="westeurope"
UNIQUE_ID=$(date +%s | tail -c 5)
KEY_VAULT_NAME="kv-alis-${UNIQUE_ID}"
APP_SERVICE_PLAN="asp-alis-learning"
BACKEND_APP_NAME="app-alis-backend-${UNIQUE_ID}"
GITHUB_REPO="https://github.com/TorstenS1/learning"

echo ""
echo "Configuration:"
echo "  Resource Group: ${RESOURCE_GROUP}"
echo "  Location: ${LOCATION}"
echo "  Key Vault: ${KEY_VAULT_NAME}"
echo "  Backend App: ${BACKEND_APP_NAME}"
echo "  GitHub Repo: ${GITHUB_REPO}"
echo ""

# Step 1: Create Resource Group
echo "[1/9] Creating Resource Group..."
az group create \
  --name "${RESOURCE_GROUP}" \
  --location "${LOCATION}" \
  --output table

# Step 2: Create Key Vault
echo "[2/9] Creating Key Vault..."
az keyvault create \
  --name "${KEY_VAULT_NAME}" \
  --resource-group "${RESOURCE_GROUP}" \
  --location "${LOCATION}" \
  --sku standard \
  --enable-rbac-authorization false \
  --output table

# Get current user object ID
CURRENT_USER_ID=$(az ad signed-in-user show --query id --output tsv)

# Grant current user permissions to manage secrets
echo "  Granting current user permissions..."
az keyvault set-policy \
  --name "${KEY_VAULT_NAME}" \
  --object-id "${CURRENT_USER_ID}" \
  --secret-permissions get list set delete \
  --output table

# Step 3: Store secrets in Key Vault
echo "[3/9] Storing secrets in Key Vault..."
az keyvault secret set \
  --vault-name "${KEY_VAULT_NAME}" \
  --name "GEMINI-API-KEY" \
  --value "${GEMINI_API_KEY}" \
  --output table

az keyvault secret set \
  --vault-name "${KEY_VAULT_NAME}" \
  --name "MONGO-URI" \
  --value "${MONGO_URI}" \
  --output table

# Step 4: Create App Service Plan (F1 Free tier)
echo "[4/9] Creating App Service Plan (F1 Free)..."
az appservice plan create \
  --name "${APP_SERVICE_PLAN}" \
  --resource-group "${RESOURCE_GROUP}" \
  --location "${LOCATION}" \
  --is-linux \
  --sku F1 \
  --output table

# Step 5: Create Web App
echo "[5/9] Creating Web App for Backend..."
az webapp create \
  --name "${BACKEND_APP_NAME}" \
  --resource-group "${RESOURCE_GROUP}" \
  --plan "${APP_SERVICE_PLAN}" \
  --runtime "PYTHON:3.11" \
  --output table

# Step 6: Enable System Managed Identity
echo "[6/9] Enabling System Managed Identity..."
PRINCIPAL_ID=$(az webapp identity assign \
  --name "${BACKEND_APP_NAME}" \
  --resource-group "${RESOURCE_GROUP}" \
  --query principalId \
  --output tsv)

echo "  Principal ID: ${PRINCIPAL_ID}"

# Wait for identity to propagate
echo "  Waiting for identity to propagate..."
sleep 10

# Step 7: Grant Web App access to Key Vault
echo "[7/9] Granting Web App access to Key Vault secrets..."
az keyvault set-policy \
  --name "${KEY_VAULT_NAME}" \
  --object-id "${PRINCIPAL_ID}" \
  --secret-permissions get list \
  --output table

# Step 8: Configure App Settings with Key Vault references
echo "[8/9] Configuring App Settings..."

# Get Key Vault secret URIs
GEMINI_SECRET_URI=$(az keyvault secret show \
  --vault-name "${KEY_VAULT_NAME}" \
  --name "GEMINI-API-KEY" \
  --query id \
  --output tsv)

MONGO_SECRET_URI=$(az keyvault secret show \
  --vault-name "${KEY_VAULT_NAME}" \
  --name "MONGO-URI" \
  --query id \
  --output tsv)

# Configure app settings
az webapp config appsettings set \
  --name "${BACKEND_APP_NAME}" \
  --resource-group "${RESOURCE_GROUP}" \
  --settings \
    GEMINI_API_KEY="@Microsoft.KeyVault(SecretUri=${GEMINI_SECRET_URI})" \
    MONGODB_URI="@Microsoft.KeyVault(SecretUri=${MONGO_SECRET_URI})" \
    USE_LLM_SIMULATION="false" \
    DEBUG="false" \
    PORT="8000" \
    CORS_ORIGINS="https://*.azurestaticapps.net" \
    SCM_DO_BUILD_DURING_DEPLOYMENT="true" \
  --output table

# Configure startup command
az webapp config set \
  --name "${BACKEND_APP_NAME}" \
  --resource-group "${RESOURCE_GROUP}" \
  --startup-file "startup.sh" \
  --output table

# Step 9: Configure GitHub deployment
echo "[9/9] Configuring GitHub deployment..."
echo ""
echo "⚠️  Manual step required:"
echo "    1. Go to Azure Portal: https://portal.azure.com"
echo "    2. Navigate to: ${BACKEND_APP_NAME} > Deployment Center"
echo "    3. Select Source: GitHub"
echo "    4. Authorize and select repository: TorstenS1/learning"
echo "    5. Select branch: main"
echo "    6. Build provider: GitHub Actions"
echo ""
echo "    OR run this command after authorizing GitHub:"
echo ""
echo "    az webapp deployment source config \\"
echo "      --name ${BACKEND_APP_NAME} \\"
echo "      --resource-group ${RESOURCE_GROUP} \\"
echo "      --repo-url ${GITHUB_REPO} \\"
echo "      --branch main \\"
echo "      --git-token YOUR_GITHUB_TOKEN"
echo ""

# Summary
echo "=========================================="
echo "✅ Infrastructure Setup Complete!"
echo "=========================================="
echo ""
echo "Backend URL: https://${BACKEND_APP_NAME}.azurewebsites.net"
echo "Health Check: https://${BACKEND_APP_NAME}.azurewebsites.net/api/health"
echo ""
echo "Next steps:"
echo "  1. Configure GitHub deployment (see above)"
echo "  2. Create GitHub Actions workflows"
echo "  3. Push to main branch to trigger deployment"
echo "  4. Set up Static Web App for frontend"
echo ""
echo "Resource Details:"
echo "  Resource Group: ${RESOURCE_GROUP}"
echo "  Key Vault: ${KEY_VAULT_NAME}"
echo "  Backend App: ${BACKEND_APP_NAME}"
echo ""
