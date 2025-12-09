#!/bin/bash
################################################################################
# ALIS Azure Deployment Script (Free Tier)
# 
# This script deploys the ALIS learning application to Azure using free tier
# services:
# - Backend: Azure App Service (F1 Free tier)
# - Frontend: Azure Static Web Apps (Free tier)
# - Secrets: Azure Key Vault (pay-per-use, ~$0.03/month)
# - Storage: Azure Storage Account (for Function App metadata)
#
# Prerequisites:
# - Azure CLI installed and logged in (az login)
# - GitHub repository: https://github.com/TorstenS1/learning
# - Environment variables: GEMINI_API_KEY, MONGO_URI
#
# Usage:
#   export GEMINI_API_KEY="your-api-key"
#   export MONGO_URI="your-mongodb-uri"
#   chmod +x deploy_to_azure.sh
#   ./deploy_to_azure.sh
################################################################################

set -e  # Exit on error


# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo ""
    echo -e "${BLUE}=========================================="
    echo -e "$1"
    echo -e "==========================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

wait_for_completion() {
    local message=$1
    local seconds=${2:-10}
    print_warning "$message"
    echo -n "Waiting $seconds seconds"
    for i in $(seq 1 $seconds); do
        echo -n "."
        sleep 1
    done
    echo ""
}

################################################################################
# CONFIGURATION
################################################################################

print_header "ALIS Azure Deployment - Configuration"

# Generate unique ID for resources
UNIQUE_ID=$(date +%s | tail -c 5)

# Resource names
RESOURCE_GROUP="rg-alis-learning"
LOCATION="westeurope"
KEY_VAULT_NAME="kv-alis-${UNIQUE_ID}"
STORAGE_ACCOUNT="stalislearning${UNIQUE_ID}"
APP_SERVICE_PLAN="asp-alis-learning"
BACKEND_APP_NAME="app-alis-backend-${UNIQUE_ID}"
STATIC_WEB_APP_NAME="stapp-alis-learning"

# GitHub configuration
GITHUB_REPO="https://github.com/TorstenS1/learning"
GITHUB_OWNER="TorstenS1"
GITHUB_REPO_NAME="learning"

# Display configuration
echo "Configuration:"
echo "  Unique ID:        ${UNIQUE_ID}"
echo "  Resource Group:   ${RESOURCE_GROUP}"
echo "  Location:         ${LOCATION}"
echo "  Key Vault:        ${KEY_VAULT_NAME}"
echo "  Storage Account:  ${STORAGE_ACCOUNT}"
echo "  Backend App:      ${BACKEND_APP_NAME}"
echo "  Static Web App:   ${STATIC_WEB_APP_NAME}"
echo "  GitHub Repo:      ${GITHUB_REPO}"
echo ""

# Validate environment variables
if [ -z "$GEMINI_API_KEY" ]; then
    print_error "GEMINI_API_KEY environment variable is not set"
    echo "Please run: export GEMINI_API_KEY=\"your-api-key\""
    exit 1
fi

if [ -z "$MONGO_URI" ]; then
    print_error "MONGO_URI environment variable is not set"
    echo "Please run: export MONGO_URI=\"your-mongodb-uri\""
    exit 1
fi

print_success "Configuration validated"

################################################################################
# STEP 0: TEST MONGODB CONNECTION
################################################################################

print_header "Step 0/10: Testing MongoDB Connection"

# Create temporary python test script
cat > test_mongo_connection.py << 'EOF'
import os
import sys
import pymongo
from pymongo.errors import ConnectionFailure, ConfigurationError

def test_mongo_connection(uri):
    print(f"Testing MongoDB connection...")
    # Mask URI for security in logs
    masked_uri = uri.split('@')[-1] if '@' in uri else '***'
    print(f"Target: ...@{masked_uri}")

    try:
        # Set a short timeout (5s) to fail fast
        client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=5000)
        
        # The ismaster command is cheap and does not require auth.
        client.admin.command('ismaster')
        
        print("✅ Successfully connected to MongoDB!")
        return True
    except ConnectionFailure as e:
        print(f"❌ Connection failed: {e}")
        return False
    except ConfigurationError as e:
        print(f"❌ Configuration error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    uri = os.environ.get("MONGO_URI")
    if not uri:
        print("❌ MONGO_URI environment variable not set")
        sys.exit(1)
    
    if test_mongo_connection(uri):
        sys.exit(0)
    else:
        sys.exit(1)
EOF

# Run the test
print_info "Running MongoDB connection test..."
if python3 test_mongo_connection.py; then
    print_success "MongoDB connection verified"
    rm test_mongo_connection.py
else
    print_error "MongoDB connection failed. Please check your MONGO_URI."
    rm test_mongo_connection.py
    exit 1
fi

# Confirm before proceeding
read -p "Do you want to proceed with deployment? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Deployment cancelled"
    exit 0
fi

################################################################################
# STEP 1: CREATE RESOURCE GROUP
################################################################################

print_header "Step 1/10: Creating Resource Group"

if az group exists --name "${RESOURCE_GROUP}" | grep -q "true"; then
    print_warning "Resource group ${RESOURCE_GROUP} already exists, skipping..."
else
    az group create \
        --name "${RESOURCE_GROUP}" \
        --location "${LOCATION}" \
        --output table
    
    print_success "Resource group created"
fi

################################################################################
# STEP 2: CREATE KEY VAULT
################################################################################

print_header "Step 2/10: Creating Key Vault"

# Check if Key Vault exists
if az keyvault show --name "${KEY_VAULT_NAME}" --resource-group "${RESOURCE_GROUP}" &>/dev/null; then
    print_warning "Key Vault ${KEY_VAULT_NAME} already exists, skipping creation..."
else
    az keyvault create \
        --name "${KEY_VAULT_NAME}" \
        --resource-group "${RESOURCE_GROUP}" \
        --location "${LOCATION}" \
        --sku standard \
        --enable-rbac-authorization false \
        --output table
    
    print_success "Key Vault created"
    
    # Wait for Key Vault to be ready
    wait_for_completion "Waiting for Key Vault to be fully provisioned" 15
fi

# Get current user object ID
CURRENT_USER_ID=$(az ad signed-in-user show --query id --output tsv)
print_info "Current user ID: ${CURRENT_USER_ID}"

# Grant current user permissions to manage secrets
print_info "Granting current user Key Vault permissions..."
az keyvault set-policy \
    --name "${KEY_VAULT_NAME}" \
    --object-id "${CURRENT_USER_ID}" \
    --secret-permissions get list set delete \
    --output table

print_success "Key Vault permissions configured"

################################################################################
# STEP 3: STORE SECRETS IN KEY VAULT
################################################################################

print_header "Step 3/10: Storing Secrets in Key Vault"

print_info "Storing GEMINI_API_KEY..."
az keyvault secret set \
    --vault-name "${KEY_VAULT_NAME}" \
    --name "GEMINI-API-KEY" \
    --value "${GEMINI_API_KEY}" \
    --output table

print_info "Storing MONGO_URI..."
az keyvault secret set \
    --vault-name "${KEY_VAULT_NAME}" \
    --name "MONGO-URI" \
    --value "${MONGO_URI}" \
    --output table

print_success "Secrets stored in Key Vault"

################################################################################
# STEP 4: CREATE STORAGE ACCOUNT
################################################################################

print_header "Step 4/10: Creating Storage Account"

if az storage account show --name "${STORAGE_ACCOUNT}" --resource-group "${RESOURCE_GROUP}" &>/dev/null; then
    print_warning "Storage account ${STORAGE_ACCOUNT} already exists, skipping..."
else
    az storage account create \
        --name "${STORAGE_ACCOUNT}" \
        --resource-group "${RESOURCE_GROUP}" \
        --location "${LOCATION}" \
        --sku Standard_LRS \
        --output table
    
    print_success "Storage account created"
    
    # Wait for storage account to be ready
    wait_for_completion "Waiting for storage account to be fully provisioned" 10
fi

################################################################################
# STEP 5: CREATE APP SERVICE PLAN (F1 FREE TIER)
################################################################################

print_header "Step 5/10: Creating App Service Plan (F1 Free Tier)"

if az appservice plan show --name "${APP_SERVICE_PLAN}" --resource-group "${RESOURCE_GROUP}" &>/dev/null; then
    print_warning "App Service Plan ${APP_SERVICE_PLAN} already exists, skipping..."
else
    az appservice plan create \
        --name "${APP_SERVICE_PLAN}" \
        --resource-group "${RESOURCE_GROUP}" \
        --location "${LOCATION}" \
        --is-linux \
        --sku F1 \
        --output table
    
    print_success "App Service Plan created (F1 Free tier)"
fi

################################################################################
# STEP 6: CREATE WEB APP FOR BACKEND
################################################################################

print_header "Step 6/10: Creating Web App for Backend"

if az webapp show --name "${BACKEND_APP_NAME}" --resource-group "${RESOURCE_GROUP}" &>/dev/null; then
    print_warning "Web App ${BACKEND_APP_NAME} already exists, skipping..."
else
    az webapp create \
        --name "${BACKEND_APP_NAME}" \
        --resource-group "${RESOURCE_GROUP}" \
        --plan "${APP_SERVICE_PLAN}" \
        --runtime "PYTHON:3.11" \
        --output table
    
    print_success "Web App created"
    
    # Wait for Web App to be ready
    wait_for_completion "Waiting for Web App to be fully provisioned" 15
fi

################################################################################
# STEP 7: ENABLE MANAGED IDENTITY AND CONFIGURE KEY VAULT ACCESS
################################################################################

print_header "Step 7/10: Configuring Managed Identity and Key Vault Access"

print_info "Enabling System Managed Identity..."
PRINCIPAL_ID=$(az webapp identity assign \
    --name "${BACKEND_APP_NAME}" \
    --resource-group "${RESOURCE_GROUP}" \
    --query principalId \
    --output tsv)

print_info "Principal ID: ${PRINCIPAL_ID}"

# Wait for identity to propagate
wait_for_completion "Waiting for managed identity to propagate in Azure AD" 20

print_info "Granting Web App access to Key Vault secrets..."
az keyvault set-policy \
    --name "${KEY_VAULT_NAME}" \
    --object-id "${PRINCIPAL_ID}" \
    --secret-permissions get list \
    --output table

print_success "Managed identity configured with Key Vault access"

################################################################################
# STEP 8: CONFIGURE APP SETTINGS
################################################################################

print_header "Step 8/10: Configuring App Settings"

# Get Key Vault secret URIs
print_info "Retrieving Key Vault secret URIs..."
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

print_info "Configuring app settings with Key Vault references..."
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

print_info "Setting custom startup file..."
az webapp config set \
    --name "${BACKEND_APP_NAME}" \
    --resource-group "${RESOURCE_GROUP}" \
    --startup-file "startup.sh" \
    --output table

# Enable basic authentication for publishing
print_info "Enabling basic authentication for deployment..."
az resource update \
    --resource-group "${RESOURCE_GROUP}" \
    --name "scm" \
    --namespace Microsoft.Web \
    --resource-type basicPublishingCredentialsPolicies \
    --parent sites/${BACKEND_APP_NAME} \
    --set properties.allow=true \
    --output table

print_success "App settings configured"

################################################################################
# STEP 9: CREATE STATIC WEB APP FOR FRONTEND
################################################################################

print_header "Step 9/10: Creating Static Web App for Frontend"

# Check if Static Web App exists (suppress errors)
STATIC_APP_EXISTS=$(az staticwebapp list \
    --resource-group "${RESOURCE_GROUP}" \
    --query "[?name=='${STATIC_WEB_APP_NAME}'].name" \
    --output tsv 2>/dev/null || echo "")

if [ -n "$STATIC_APP_EXISTS" ]; then
    print_warning "Static Web App ${STATIC_WEB_APP_NAME} already exists, skipping creation..."
else
    print_info "Creating Static Web App..."
    az staticwebapp create \
        --name "${STATIC_WEB_APP_NAME}" \
        --resource-group "${RESOURCE_GROUP}" \
        --location "${LOCATION}" \
        --sku Free \
        --output table
    
    print_success "Static Web App created"
    
    # Wait for Static Web App to be ready
    wait_for_completion "Waiting for Static Web App to be fully provisioned" 30
fi

# Confirm before proceeding
read -p "Do you want to proceed with deployment? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Deployment cancelled"
    exit 0
fi


# Get deployment token
print_info "Retrieving Static Web App deployment token..."
STATIC_WEB_APP_TOKEN=$(az staticwebapp secrets list \
    --name "${STATIC_WEB_APP_NAME}" \
    --resource-group "${RESOURCE_GROUP}" \
    --query "properties.apiKey" \
    --output tsv)

# Get Static Web App URL
STATIC_WEB_APP_URL=$(az staticwebapp show \
    --name "${STATIC_WEB_APP_NAME}" \
    --resource-group "${RESOURCE_GROUP}" \
    --query "defaultHostname" \
    --output tsv)

print_success "Static Web App ready at: https://${STATIC_WEB_APP_URL}"

################################################################################
# STEP 10: GET PUBLISH PROFILE FOR GITHUB ACTIONS
################################################################################

print_header "Step 10/10: Retrieving Publish Profile"

print_info "Downloading publish profile..."
az webapp deployment list-publishing-profiles \
    --name "${BACKEND_APP_NAME}" \
    --resource-group "${RESOURCE_GROUP}" \
    --xml > publish-profile.xml

print_success "Publish profile saved to: publish-profile.xml"

################################################################################
# DEPLOYMENT SUMMARY
################################################################################

print_header "✅ DEPLOYMENT COMPLETE!"

echo "Resource Summary:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📦 Resource Group:    ${RESOURCE_GROUP}"
echo "🔐 Key Vault:         ${KEY_VAULT_NAME}"
echo "💾 Storage Account:   ${STORAGE_ACCOUNT}"
echo "🖥️  Backend App:       ${BACKEND_APP_NAME}"
echo "   URL:              https://${BACKEND_APP_NAME}.azurewebsites.net"
echo "   Health Check:     https://${BACKEND_APP_NAME}.azurewebsites.net/api/health"
echo ""
echo "🌐 Frontend App:      ${STATIC_WEB_APP_NAME}"
echo "   URL:              https://${STATIC_WEB_APP_URL}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

print_header "📋 NEXT STEPS - GitHub Configuration"

echo "To complete the deployment, configure GitHub Actions:"
echo ""
echo "1️⃣  Add GitHub Repository Secrets:"
echo "   Go to: https://github.com/${GITHUB_OWNER}/${GITHUB_REPO_NAME}/settings/secrets/actions"
echo ""
echo "   Add these 3 secrets:"
echo ""
echo "   Name: UNIQUE_ID"
echo "   Value: ${UNIQUE_ID}"
echo ""
echo "   Name: AZURE_STATIC_WEB_APPS_API_TOKEN"
echo "   Value: ${STATIC_WEB_APP_TOKEN}"
echo ""
echo "   Name: AZURE_WEBAPP_PUBLISH_PROFILE"
echo "   Value: (Copy entire content from publish-profile.xml)"
echo "   Command to view: cat publish-profile.xml"
echo ""
echo "2️⃣  Commit and Push Deployment Files:"
echo "   git add .github/workflows/"
echo "   git add frontend/staticwebapp.config.json"
echo "   git add DEPLOYMENT.md"
echo "   git commit -m \"Add Azure deployment configuration\""
echo "   git push origin main"
echo ""
echo "3️⃣  Monitor Deployment:"
echo "   GitHub Actions: https://github.com/${GITHUB_OWNER}/${GITHUB_REPO_NAME}/actions"
echo ""
echo "4️⃣  Verify Deployment:"
echo "   Backend:  curl https://${BACKEND_APP_NAME}.azurewebsites.net/api/health"
echo "   Frontend: https://${STATIC_WEB_APP_URL}"
echo ""

print_header "💰 Cost Estimate"

echo "All services are on free tiers:"
echo "  • App Service (F1):        \$0/month (60 CPU min/day limit)"
echo "  • Static Web Apps:         \$0/month (100 GB bandwidth/month)"
echo "  • Storage Account:         \$0/month (minimal usage)"
echo "  • Key Vault:               ~\$0.03/month (transaction-based)"
echo ""
echo "  Total estimated cost:      < \$1/month"
echo ""

print_header "🗑️  Cleanup (Optional)"

echo "To delete all resources:"
echo "  az group delete --name ${RESOURCE_GROUP} --yes --no-wait"
echo ""

print_success "Deployment script completed successfully!"
echo ""
echo "Save these values for reference:"
echo "  UNIQUE_ID=${UNIQUE_ID}"
echo "  BACKEND_URL=https://${BACKEND_APP_NAME}.azurewebsites.net"
echo "  FRONTEND_URL=https://${STATIC_WEB_APP_URL}"
echo ""
