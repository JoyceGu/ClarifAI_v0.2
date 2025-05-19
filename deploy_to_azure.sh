#!/bin/bash
# ClarifAI Azure Deployment Script - Optimized Version

if [ -f .env ]; then
  echo "Loading environment variables from .env file..."
  export $(grep -v '^#' .env | xargs)
fi

echo "======== ClarifAI Azure Deployment Script - Optimized Version ========"

# 添加时间戳变量
TIMESTAMP=$(date +%Y%m%d%H%M%S)
echo "Deployment timestamp: $TIMESTAMP"

# Configuration variables - modify these values as needed
RESOURCE_GROUP="clarifai-test-0517"
LOCATION="westus2"  # Changed to westus because westus3 may have quota limitations
APP_NAME="clarifai-app"
SQL_SERVER_NAME="clarifai-sql-server"
SQL_DB_NAME="clarifaidb"
SQL_ADMIN_USER="clarifaiadmin"
SQL_ADMIN_PASSWORD="P@ssw0rd123"  # Fixed password without version
STORAGE_ACCOUNT_NAME="clarifaist$(date +%s | sha1sum | head -c 8)"  # Ensure uniqueness
CONTAINER_NAME="file-uploads"
OPENAI_NAME="aoai-clarifai-test-0517"
INSIGHTS_NAME="clarifai-insights"
KEYVAULT_NAME="clarifai-kv"
APP_SERVICE_PLAN="clarifai-service-plan-${TIMESTAMP}"

echo "Using the following resource names:"
echo "Resource Group: $RESOURCE_GROUP"
echo "App Name: $APP_NAME"
echo "SQL Server: $SQL_SERVER_NAME"
echo "Storage Account: $STORAGE_ACCOUNT_NAME"
echo "App Service Plan: $APP_SERVICE_PLAN"

# Create resource group
# echo "Creating resource group $RESOURCE_GROUP in $LOCATION..."
# az group create --name $RESOURCE_GROUP --location $LOCATION

# Create Azure SQL Server and Database
echo "Creating Azure SQL Server and Database..."
az sql server create \
    --name $SQL_SERVER_NAME \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --admin-user $SQL_ADMIN_USER \
    --admin-password $SQL_ADMIN_PASSWORD

# Configure firewall rules to allow Azure services access
az sql server firewall-rule create \
    --resource-group $RESOURCE_GROUP \
    --server $SQL_SERVER_NAME \
    --name AllowAzureServices \
    --start-ip-address 0.0.0.0 \
    --end-ip-address 0.0.0.0

# Create database
az sql db create \
    --resource-group $RESOURCE_GROUP \
    --server $SQL_SERVER_NAME \
    --name $SQL_DB_NAME \
    --edition Basic \
    --capacity 5

# Get database connection string
SQL_CONNECTION_STRING=$(az sql db show-connection-string \
    --client odbc \
    --name $SQL_DB_NAME \
    --server $SQL_SERVER_NAME \
    | sed "s/<username>/$SQL_ADMIN_USER/;s/<password>/$SQL_ADMIN_PASSWORD/")

# Create Storage Account
echo "Creating Azure Storage Account..."
az storage account create \
    --name $STORAGE_ACCOUNT_NAME \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --sku Standard_LRS

# Create Blob container
STORAGE_KEY=$(az storage account keys list \
    --account-name $STORAGE_ACCOUNT_NAME \
    --resource-group $RESOURCE_GROUP \
    --query "[0].value" -o tsv)

az storage container create \
    --name $CONTAINER_NAME \
    --account-name $STORAGE_ACCOUNT_NAME \
    --account-key "$STORAGE_KEY" \
    --public-access off

# Get storage connection string
STORAGE_CONNECTION_STRING=$(az storage account show-connection-string \
    --name $STORAGE_ACCOUNT_NAME \
    --resource-group $RESOURCE_GROUP \
    --query connectionString \
    --output tsv)

# Install necessary extensions
echo "Installing required extensions..."
az extension add --name application-insights --yes

# Create Application Insights
echo "Creating Application Insights..."
az monitor app-insights component create \
    --app $INSIGHTS_NAME \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --application-type web

# Get Application Insights connection string
APPINSIGHTS_CONNECTION_STRING=$(az monitor app-insights component show \
    --app $INSIGHTS_NAME \
    --resource-group $RESOURCE_GROUP \
    --query connectionString \
    --output tsv)

# Create Key Vault with access policy mode (non-RBAC)
echo "Creating Azure Key Vault..."
USER_OBJECTID=$(az ad signed-in-user show --query id --output tsv)

az keyvault create \
    --name $KEYVAULT_NAME \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --enable-rbac-authorization false

# Set access policy
az keyvault set-policy \
    --name $KEYVAULT_NAME \
    --resource-group $RESOURCE_GROUP \
    --object-id $USER_OBJECTID \
    --secret-permissions get list set delete backup restore recover \
    --key-permissions get list create delete import update backup restore recover

# Store sensitive information in Key Vault
echo "Storing sensitive information in Key Vault..."
az keyvault secret set --vault-name $KEYVAULT_NAME --name "SqlConnectionString" --value "$SQL_CONNECTION_STRING"
az keyvault secret set --vault-name $KEYVAULT_NAME --name "StorageConnectionString" --value "$STORAGE_CONNECTION_STRING"
az keyvault secret set --vault-name $KEYVAULT_NAME --name "AppInsightsConnectionString" --value "$APPINSIGHTS_CONNECTION_STRING"

# Create App Service Plan - use B1 Basic tier for better performance
echo "Creating App Service Plan..."
az appservice plan create \
    --name $APP_SERVICE_PLAN \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --sku B1 \
    --is-linux

# Create Web App
echo "Creating Web App..."
az webapp create \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --plan $APP_SERVICE_PLAN \
    --runtime "PYTHON:3.11"

# Ensure Web App creation success
echo "Waiting for Web App to be ready..."
sleep 30

# Configure Web App settings
echo "Configuring Web App settings..."
az webapp config set \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --startup-file "gunicorn --bind=0.0.0.0 --timeout=120 --workers=2 run:app"

# Enable local cache to improve performance and build speed
echo "Enabling Local Cache for better performance..."
az webapp config appsettings set \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --settings WEBSITE_LOCAL_CACHE_OPTION=Always

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

# Set environment variables
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
    DEPLOYMENT_TIMESTAMP="${TIMESTAMP}"

# Enable Web App managed identity
echo "Enabling Managed Identity for Web App..."
az webapp identity assign \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP

# Get managed identity object ID
APP_OBJECTID=$(az webapp identity show \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query principalId \
    --output tsv)

# If managed identity is retrieved, authorize Web App access to Key Vault
if [ ! -z "$APP_OBJECTID" ]; then
    echo "Granting Web App access to Key Vault..."
    az keyvault set-policy \
        --name $KEYVAULT_NAME \
        --resource-group $RESOURCE_GROUP \
        --object-id $APP_OBJECTID \
        --secret-permissions get list
else
    echo "Warning: Could not retrieve Web App managed identity."
fi

# 注释掉这部分代码
# echo "Creating a staging deployment slot..."
# az webapp deployment slot create \
#     --name $APP_NAME \
#     --resource-group $RESOURCE_GROUP \
#     --slot staging

# 也注释掉配置部署槽的代码
# az webapp config set \
#     --name $APP_NAME \
#     --resource-group $RESOURCE_GROUP \
#     --slot staging \
#     --startup-file "gunicorn --bind=0.0.0.0 --workers=2 'run:app'"

# az webapp config appsettings set \
#     --name $APP_NAME \
#     --resource-group $RESOURCE_GROUP \
#     --slot staging \
#     --settings $(az webapp config appsettings list --name $APP_NAME --resource-group $RESOURCE_GROUP --query "[].{name:name, value:value}" --output tsv | sed 's/\t/=/' | tr '\n' ' ')

echo "======== Deployment settings optimization completed ========"
echo "Deployment setup complete! Now you can deploy your code using the following command:"
echo "az webapp deployment source config-zip --resource-group $RESOURCE_GROUP --name $APP_NAME --src deployment/clarifai_app.zip"
echo ""
echo "Or use deployment slots for zero-downtime deployment:"
echo "az webapp deployment source config-zip --resource-group $RESOURCE_GROUP --name $APP_NAME --slot staging --src deployment/clarifai_app.zip"
echo "az webapp deployment slot swap --resource-group $RESOURCE_GROUP --name $APP_NAME --slot staging --target-slot production"
echo ""
echo "Resource Group: $RESOURCE_GROUP"
echo "App Name: $APP_NAME"
echo "SQL Server: $SQL_SERVER_NAME"
echo "SQL Database: $SQL_DB_NAME"
echo "Storage Account: $STORAGE_ACCOUNT_NAME"
echo "Application Insights: $INSIGHTS_NAME"
echo "Key Vault: $KEYVAULT_NAME"
echo ""
echo "Please update your .env file with Azure OpenAI and Microsoft Entra ID settings manually."

# # 升级App Service Plan（如有需要）
# az appservice plan update \
#     --name <your-app-service-plan-name> \
#     --resource-group clarifai-test-0517 \
#     --sku S1 

az webapp config appsettings set \
    --name clarifai-app \
    --resource-group clarifai-test-0517 \
    --settings \
    AZURE_OPENAI_API_KEY="${AZURE_OPENAI_API_KEY}" \
    AZURE_OPENAI_ENDPOINT="${AZURE_OPENAI_ENDPOINT}" \
    AZURE_OPENAI_DEPLOYMENT_NAME="${AZURE_OPENAI_DEPLOYMENT_NAME}" \
    AZURE_OPENAI_API_VERSION="${AZURE_OPENAI_API_VERSION}"