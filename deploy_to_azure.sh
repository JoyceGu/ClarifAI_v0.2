#!/bin/bash
# ClarifAI Azure Deployment Script - Optimized Version

if [ -f .env ]; then
  echo "Loading environment variables from .env file..."
  export $(grep -v '^#' .env | xargs)
fi

echo "======== ClarifAI Azure Deployment Script - Optimized Version ========"

# Configuration variables - these should match your existing Azure resources
RESOURCE_GROUP="clarifai-test-0517"
LOCATION="westus2"
APP_NAME="clarifai-app"
SQL_SERVER_NAME="clarifai-sql-server"
SQL_DB_NAME="clarifaidb"
SQL_ADMIN_USER="clarifaiadmin"

# Security improvement: Get password from environment variable or use existing one
SQL_ADMIN_PASSWORD="${SQL_PASSWORD:-$(openssl rand -base64 16)}"
echo "Using SQL password: $SQL_ADMIN_PASSWORD (Please record this securely!)"

STORAGE_ACCOUNT_NAME="clarifaistfb9a4349"
CONTAINER_NAME="file-uploads"
OPENAI_NAME="aoai-clarifai-0517"
INSIGHTS_NAME="clarifai-insights"
KEYVAULT_NAME="clarifai-kv"
APP_SERVICE_PLAN="clarifai-service-plan-"

echo "Using the following resource names:"
echo "Resource Group: $RESOURCE_GROUP"
echo "App Name: $APP_NAME"
echo "SQL Server: $SQL_SERVER_NAME"
echo "Storage Account: $STORAGE_ACCOUNT_NAME"
echo "Key Vault: $KEYVAULT_NAME"
echo "App Service Plan: $APP_SERVICE_PLAN"

# Verify required environment variables before deployment
if [ -z "$AZURE_OPENAI_API_KEY" ] || [ -z "$AZURE_OPENAI_ENDPOINT" ] || [ -z "$AZURE_OPENAI_DEPLOYMENT_NAME" ] || [ -z "$AZURE_OPENAI_API_VERSION" ]; then
  echo "ERROR: Azure OpenAI environment variables are not fully set. Please ensure the following variables are set:"
  echo "- AZURE_OPENAI_API_KEY"
  echo "- AZURE_OPENAI_ENDPOINT"
  echo "- AZURE_OPENAI_DEPLOYMENT_NAME"
  echo "- AZURE_OPENAI_API_VERSION"
  echo "Continuing with script execution, but the application may not function correctly."
fi

# Add error handling function
handle_error() {
  local exit_code=$1
  local error_message=$2
  
  if [ $exit_code -ne 0 ]; then
    echo "ERROR: $error_message"
    echo "Continuing with the rest of the script..."
  fi
}

# Function to check if a resource exists
resource_exists() {
  local resource_type=$1
  local resource_name=$2
  local resource_group=$3
  
  if [ -z "$resource_group" ]; then
    az $resource_type show --name "$resource_name" &>/dev/null
  else
    az $resource_type show --name "$resource_name" --resource-group "$resource_group" &>/dev/null
  fi
  
  return $?
}

# Check if resource group exists, if not create it
echo "Checking if resource group $RESOURCE_GROUP exists..."
if ! resource_exists "group" "$RESOURCE_GROUP"; then
  echo "Resource group does not exist, creating it in $LOCATION..."
  az group create --name $RESOURCE_GROUP --location $LOCATION
  handle_error $? "Failed to create resource group"
else
  echo "Resource group $RESOURCE_GROUP already exists."
fi

# Check if SQL Server exists, if not create it
echo "Checking if SQL Server $SQL_SERVER_NAME exists..."
if ! resource_exists "sql server" "$SQL_SERVER_NAME" "$RESOURCE_GROUP"; then
  echo "SQL Server does not exist, creating it..."
  az sql server create \
      --name $SQL_SERVER_NAME \
      --resource-group $RESOURCE_GROUP \
      --location $LOCATION \
      --admin-user $SQL_ADMIN_USER \
      --admin-password "$SQL_ADMIN_PASSWORD"
  handle_error $? "Failed to create SQL server"
  
  # Configure firewall rules to allow Azure services access
  echo "Configuring SQL Server firewall rules..."
  az sql server firewall-rule create \
      --resource-group $RESOURCE_GROUP \
      --server $SQL_SERVER_NAME \
      --name AllowAzureServices \
      --start-ip-address 0.0.0.0 \
      --end-ip-address 0.0.0.0
  handle_error $? "Failed to configure SQL firewall rules"
else
  echo "SQL Server $SQL_SERVER_NAME already exists."
fi

# Check if database exists, if not create it
echo "Checking if SQL Database $SQL_DB_NAME exists..."
if ! az sql db show --resource-group $RESOURCE_GROUP --server $SQL_SERVER_NAME --name $SQL_DB_NAME &>/dev/null; then
  echo "SQL Database does not exist, creating it..."
  az sql db create \
      --resource-group $RESOURCE_GROUP \
      --server $SQL_SERVER_NAME \
      --name $SQL_DB_NAME \
      --edition Basic \
      --capacity 5
  handle_error $? "Failed to create SQL database"
else
  echo "SQL Database $SQL_DB_NAME already exists."
fi

# Get database connection string
echo "Getting SQL connection string..."
SQL_CONNECTION_STRING=$(az sql db show-connection-string \
    --client odbc \
    --name $SQL_DB_NAME \
    --server $SQL_SERVER_NAME \
    | sed "s/<username>/$SQL_ADMIN_USER/;s/<password>/$SQL_ADMIN_PASSWORD/")
handle_error $? "Failed to get SQL connection string"

# Check if storage account exists, if not create it
echo "Checking if Storage Account $STORAGE_ACCOUNT_NAME exists..."
if ! resource_exists "storage account" "$STORAGE_ACCOUNT_NAME" "$RESOURCE_GROUP"; then
  echo "Storage Account does not exist, creating it..."
  az storage account create \
      --name $STORAGE_ACCOUNT_NAME \
      --resource-group $RESOURCE_GROUP \
      --location $LOCATION \
      --sku Standard_LRS
  handle_error $? "Failed to create storage account"
else
  echo "Storage Account $STORAGE_ACCOUNT_NAME already exists."
fi

# Get storage account key
echo "Getting storage account key..."
STORAGE_KEY=$(az storage account keys list \
    --account-name $STORAGE_ACCOUNT_NAME \
    --resource-group $RESOURCE_GROUP \
    --query "[0].value" -o tsv)
handle_error $? "Failed to get storage account key"

# Check if container exists, if not create it
echo "Checking if blob container $CONTAINER_NAME exists..."
if ! az storage container show --name $CONTAINER_NAME --account-name $STORAGE_ACCOUNT_NAME --account-key "$STORAGE_KEY" &>/dev/null; then
  echo "Blob container does not exist, creating it..."
  az storage container create \
      --name $CONTAINER_NAME \
      --account-name $STORAGE_ACCOUNT_NAME \
      --account-key "$STORAGE_KEY" \
      --public-access off
  handle_error $? "Failed to create storage container"
else
  echo "Blob container $CONTAINER_NAME already exists."
fi

# Get storage connection string
echo "Getting storage connection string..."
STORAGE_CONNECTION_STRING=$(az storage account show-connection-string \
    --name $STORAGE_ACCOUNT_NAME \
    --resource-group $RESOURCE_GROUP \
    --query connectionString \
    --output tsv)
handle_error $? "Failed to get storage connection string"

# Install necessary extensions if needed
echo "Ensuring Application Insights extension is installed..."
az extension add --name application-insights --yes 2>/dev/null

# Check if Application Insights exists, if not create it
echo "Checking if Application Insights $INSIGHTS_NAME exists..."
if ! az monitor app-insights component show --app $INSIGHTS_NAME --resource-group $RESOURCE_GROUP &>/dev/null; then
  echo "Application Insights does not exist, creating it..."
  az monitor app-insights component create \
      --app $INSIGHTS_NAME \
      --resource-group $RESOURCE_GROUP \
      --location $LOCATION \
      --application-type web
  handle_error $? "Failed to create Application Insights"
else
  echo "Application Insights $INSIGHTS_NAME already exists."
fi

# Get Application Insights connection string
echo "Getting Application Insights connection string..."
APPINSIGHTS_CONNECTION_STRING=$(az monitor app-insights component show \
    --app $INSIGHTS_NAME \
    --resource-group $RESOURCE_GROUP \
    --query connectionString \
    --output tsv)
handle_error $? "Failed to get Application Insights connection string"

# Check if Key Vault exists
echo "Checking if Key Vault $KEYVAULT_NAME exists..."
if ! az keyvault show --name $KEYVAULT_NAME &>/dev/null; then
  echo "Key Vault does not exist, creating it..."
  # Key Vault names need to be globally unique
  KV_CHECK=$(az keyvault list --query "[?name=='$KEYVAULT_NAME'].name" -o tsv)
  if [ ! -z "$KV_CHECK" ]; then
    echo "WARNING: Key Vault name '$KEYVAULT_NAME' exists but isn't in your subscription."
    TIMESTAMP=$(date +%s)
    RANDOM_SUFFIX=$(cat /dev/urandom | tr -dc 'a-z0-9' | fold -w 8 | head -n 1)
    KEYVAULT_NAME="clarifai-kv-${TIMESTAMP}-${RANDOM_SUFFIX}"
    echo "Using new Key Vault name: $KEYVAULT_NAME"
  fi
  
  # Get user object ID for access policy
  USER_OBJECTID=$(az ad signed-in-user show --query id --output tsv)
  handle_error $? "Failed to get user object ID"
  
  # Create Key Vault
  az keyvault create \
      --name $KEYVAULT_NAME \
      --resource-group $RESOURCE_GROUP \
      --location $LOCATION \
      --enable-rbac-authorization false
  handle_error $? "Failed to create Key Vault"
  
  # Set access policy
  echo "Setting Key Vault access policy..."
  az keyvault set-policy \
      --name $KEYVAULT_NAME \
      --resource-group $RESOURCE_GROUP \
      --object-id $USER_OBJECTID \
      --secret-permissions get list set delete backup restore recover \
      --key-permissions get list create delete import update backup restore recover
  handle_error $? "Failed to set Key Vault access policy"
else
  echo "Key Vault $KEYVAULT_NAME already exists."
  # Update access policy to ensure current user has access
  USER_OBJECTID=$(az ad signed-in-user show --query id --output tsv)
  echo "Updating Key Vault access policy for current user..."
  az keyvault set-policy \
      --name $KEYVAULT_NAME \
      --resource-group $RESOURCE_GROUP \
      --object-id $USER_OBJECTID \
      --secret-permissions get list set delete backup restore recover \
      --key-permissions get list create delete import update backup restore recover
  handle_error $? "Failed to update Key Vault access policy"
fi

# Store or update sensitive information in Key Vault
echo "Storing/updating sensitive information in Key Vault..."
az keyvault secret set --vault-name $KEYVAULT_NAME --name "SqlConnectionString" --value "$SQL_CONNECTION_STRING"
az keyvault secret set --vault-name $KEYVAULT_NAME --name "StorageConnectionString" --value "$STORAGE_CONNECTION_STRING"
az keyvault secret set --vault-name $KEYVAULT_NAME --name "AppInsightsConnectionString" --value "$APPINSIGHTS_CONNECTION_STRING"
handle_error $? "Failed to store secrets in Key Vault"

# Check if App Service Plan exists, if not create it
echo "Checking if App Service Plan $APP_SERVICE_PLAN exists..."
if ! resource_exists "appservice plan" "$APP_SERVICE_PLAN" "$RESOURCE_GROUP"; then
  echo "App Service Plan does not exist, creating it..."
  az appservice plan create \
      --name $APP_SERVICE_PLAN \
      --resource-group $RESOURCE_GROUP \
      --location $LOCATION \
      --sku B3 \
      --is-linux
  handle_error $? "Failed to create App Service Plan"
else
  echo "App Service Plan $APP_SERVICE_PLAN already exists."
fi

# Check if Web App exists, if not create it
echo "Checking if Web App $APP_NAME exists..."
if ! resource_exists "webapp" "$APP_NAME" "$RESOURCE_GROUP"; then
  echo "Web App does not exist, creating it..."
  az webapp create \
      --name $APP_NAME \
      --resource-group $RESOURCE_GROUP \
      --plan $APP_SERVICE_PLAN \
      --runtime "PYTHON:3.12"
  handle_error $? "Failed to create Web App"
  
  # Ensure Web App creation success
  echo "Waiting for Web App to be ready..."
  sleep 30
else
  echo "Web App $APP_NAME already exists."
fi

# Configure Web App settings
echo "Configuring Web App settings..."
az webapp config set \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --startup-file "gunicorn --bind=0.0.0.0:8000 run:app"
handle_error $? "Failed to configure Web App settings"

# Enable local cache to improve performance and build speed
echo "Enabling Local Cache for better performance..."
az webapp config appsettings set \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --settings WEBSITE_LOCAL_CACHE_OPTION=Always
handle_error $? "Failed to enable local cache"

# Optimize build settings
echo "Optimizing build settings..."
az webapp config appsettings set \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --settings \
    SCM_DO_BUILD_DURING_DEPLOYMENT=true \
    ENABLE_ORYX_BUILD=true \
    PRE_BUILD_COMMAND="pip install --upgrade pip pip-tools" \
    POST_BUILD_COMMAND="flask db upgrade"
handle_error $? "Failed to set build settings"

# Set environment variables
echo "Setting Web App environment variables..."
az webapp config appsettings set \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --settings \
    FLASK_APP=run.py \
    FLASK_ENV=production \
    PYTHONUNBUFFERED=1 \
    SECRET_KEY="$(openssl rand -hex 24)" \
    DATABASE_URL="mssql+pymssql://${SQL_ADMIN_USER}:${SQL_ADMIN_PASSWORD}@${SQL_SERVER_NAME}.database.windows.net:1433/${SQL_DB_NAME}" \
    AZURE_STORAGE_CONNECTION_STRING="${STORAGE_CONNECTION_STRING}" \
    AZURE_STORAGE_CONTAINER_NAME=$CONTAINER_NAME \
    USE_AZURE_STORAGE=true \
    APPLICATIONINSIGHTS_CONNECTION_STRING="${APPINSIGHTS_CONNECTION_STRING}" \
    APPLICATIONINSIGHTS_ROLE_NAME=clarifai-webapp \
    AZURE_KEY_VAULT_URL="https://${KEYVAULT_NAME}.vault.azure.net/" \
    WEBSITE_MOUNT_ENABLED=1 \
    LOG_TO_STDOUT=true \
    SSL_REDIRECT=true \
    DEPLOYMENT_TIMESTAMP="$(date +%Y%m%d%H%M%S)"
handle_error $? "Failed to set Web App environment variables"

# Enable or update Web App managed identity
echo "Enabling/updating Managed Identity for Web App..."
az webapp identity assign \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP
handle_error $? "Failed to enable managed identity"

# Get managed identity object ID
APP_OBJECTID=$(az webapp identity show \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query principalId \
    --output tsv)
handle_error $? "Failed to get Web App identity object ID"

# If managed identity is retrieved, authorize Web App access to Key Vault
if [ ! -z "$APP_OBJECTID" ]; then
    echo "Granting Web App access to Key Vault..."
    az keyvault set-policy \
        --name $KEYVAULT_NAME \
        --resource-group $RESOURCE_GROUP \
        --object-id $APP_OBJECTID \
        --secret-permissions get list
    handle_error $? "Failed to grant Web App access to Key Vault"
else
    echo "Warning: Could not retrieve Web App managed identity."
fi

# Set OpenAI environment variables
echo "Setting Azure OpenAI environment variables..."
az webapp config appsettings set \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --settings \
    AZURE_OPENAI_API_KEY="${AZURE_OPENAI_API_KEY}" \
    AZURE_OPENAI_ENDPOINT="${AZURE_OPENAI_ENDPOINT}" \
    AZURE_OPENAI_DEPLOYMENT_NAME="${AZURE_OPENAI_DEPLOYMENT_NAME}" \
    AZURE_OPENAI_API_VERSION="${AZURE_OPENAI_API_VERSION}"
handle_error $? "Failed to set OpenAI environment variables"

# Create a deployment info file for future reference
echo "Creating deployment info file..."
cat > deployment_info.txt << EOF
Deployment Information ($(date +%Y-%m-%d-%H:%M:%S))
=====================================
Resource Group: $RESOURCE_GROUP
App Name: $APP_NAME
SQL Server: $SQL_SERVER_NAME
SQL Database: $SQL_DB_NAME
Storage Account: $STORAGE_ACCOUNT_NAME
Application Insights: $INSIGHTS_NAME
Key Vault: $KEYVAULT_NAME

Deployment Command:
az webapp deploy --resource-group $RESOURCE_GROUP --name $APP_NAME --src-path deployment/clarifai_app.zip --type zip

IMPORTANT: Keep this information secure for future reference.
EOF

# Output deployment information
echo "======== Deployment Setup Complete ========"
echo "Deployment setup complete! Now you can deploy your code using the following command:"
echo "az webapp deploy --resource-group $RESOURCE_GROUP --name $APP_NAME --src-path deployment/clarifai_app.zip --type zip"
echo ""
echo "Resource Information:"
echo "Resource Group: $RESOURCE_GROUP"
echo "App Name: $APP_NAME"
echo "SQL Server: $SQL_SERVER_NAME"
echo "SQL Database: $SQL_DB_NAME"
echo "Storage Account: $STORAGE_ACCOUNT_NAME"
echo "Application Insights: $INSIGHTS_NAME"
echo "Key Vault: $KEYVAULT_NAME"
echo ""
echo "To view app settings, use:"
echo "az webapp config appsettings list --name $APP_NAME --resource-group $RESOURCE_GROUP"
echo ""
echo "Deployment information has been saved to deployment_info.txt"
echo "Please save this information in a secure location for future operations and maintenance."