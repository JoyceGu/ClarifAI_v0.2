#!/bin/bash
# ClarifAI Azure部署脚本

# 配置变量 - 请根据需要修改这些值
RESOURCE_GROUP="clarifai-resources"
LOCATION="westus3"  # 改为West US3
APP_NAME="clarifai-app"
SQL_SERVER_NAME="clarifai-sql-server"
SQL_DB_NAME="clarifaidb"
SQL_ADMIN_USER="clarifaiadmin"
SQL_ADMIN_PASSWORD="P@ssw0rd$(date +%s)"  # 自动生成随机密码
STORAGE_ACCOUNT_NAME="clarifaistorage$(date +%s | sha1sum | head -c 8)"  # 确保唯一性
CONTAINER_NAME="file-uploads"
OPENAI_NAME="clarifai-openai"
INSIGHTS_NAME="clarifai-insights"
KEYVAULT_NAME="clarifai-keyvault"

# 创建资源组
echo "Creating resource group $RESOURCE_GROUP in $LOCATION..."
az group create --name $RESOURCE_GROUP --location $LOCATION

# 创建Azure SQL Server和数据库
echo "Creating Azure SQL Server and Database..."
az sql server create \
    --name $SQL_SERVER_NAME \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --admin-user $SQL_ADMIN_USER \
    --admin-password $SQL_ADMIN_PASSWORD

# 配置防火墙规则允许Azure服务访问
az sql server firewall-rule create \
    --resource-group $RESOURCE_GROUP \
    --server $SQL_SERVER_NAME \
    --name AllowAzureServices \
    --start-ip-address 0.0.0.0 \
    --end-ip-address 0.0.0.0

# 创建数据库
az sql db create \
    --resource-group $RESOURCE_GROUP \
    --server $SQL_SERVER_NAME \
    --name $SQL_DB_NAME \
    --edition Basic \
    --capacity 5

# 获取数据库连接字符串
SQL_CONNECTION_STRING=$(az sql db show-connection-string \
    --client odbc \
    --name $SQL_DB_NAME \
    --server $SQL_SERVER_NAME \
    | sed "s/<username>/$SQL_ADMIN_USER/;s/<password>/$SQL_ADMIN_PASSWORD/")

# 创建Storage Account
echo "Creating Azure Storage Account..."
az storage account create \
    --name $STORAGE_ACCOUNT_NAME \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --sku Standard_LRS

# 创建Blob容器
STORAGE_KEY=$(az storage account keys list \
    --account-name $STORAGE_ACCOUNT_NAME \
    --resource-group $RESOURCE_GROUP \
    --query "[0].value" -o tsv)

az storage container create \
    --name $CONTAINER_NAME \
    --account-name $STORAGE_ACCOUNT_NAME \
    --account-key "$STORAGE_KEY" \
    --public-access off

# 获取存储连接字符串
STORAGE_CONNECTION_STRING=$(az storage account show-connection-string \
    --name $STORAGE_ACCOUNT_NAME \
    --resource-group $RESOURCE_GROUP \
    --query connectionString \
    --output tsv)

# 创建Application Insights
echo "Creating Application Insights..."
az monitor app-insights component create \
    --app $INSIGHTS_NAME \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --application-type web

# 获取Application Insights连接字符串
APPINSIGHTS_CONNECTION_STRING=$(az monitor app-insights component show \
    --app $INSIGHTS_NAME \
    --resource-group $RESOURCE_GROUP \
    --query connectionString \
    --output tsv)

# 创建Key Vault并为当前用户授权
echo "Creating Azure Key Vault..."
USER_OBJECTID=$(az ad signed-in-user show --query id --output tsv)

az keyvault create \
    --name $KEYVAULT_NAME \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION

az keyvault set-policy \
    --name $KEYVAULT_NAME \
    --resource-group $RESOURCE_GROUP \
    --object-id $USER_OBJECTID \
    --secret-permissions get list set delete backup restore recover \
    --key-permissions get list create delete import update backup restore recover

# 存储敏感信息到Key Vault
echo "Storing sensitive information in Key Vault..."
az keyvault secret set --vault-name $KEYVAULT_NAME --name "SqlConnectionString" --value "$SQL_CONNECTION_STRING"
az keyvault secret set --vault-name $KEYVAULT_NAME --name "StorageConnectionString" --value "$STORAGE_CONNECTION_STRING"
az keyvault secret set --vault-name $KEYVAULT_NAME --name "AppInsightsConnectionString" --value "$APPINSIGHTS_CONNECTION_STRING"

# 创建App Service Plan
echo "Creating App Service Plan..."
az appservice plan create \
    --name clarifai-service-plan \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --sku B1

# 创建Web App
echo "Creating Web App..."
az webapp create \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --plan clarifai-service-plan \
    --runtime "PYTHON:3.9"

# 配置Web App设置
echo "Configuring Web App settings..."
az webapp config set \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --startup-file "gunicorn --bind=0.0.0.0 --workers=2 'run:app'"

# 设置环境变量
az webapp config appsettings set \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --settings \
    FLASK_APP=run.py \
    FLASK_ENV=production \
    SECRET_KEY="$(openssl rand -hex 24)" \
    DATABASE_URL="mssql+pymssql://${SQL_ADMIN_USER}:${SQL_ADMIN_PASSWORD}@${SQL_SERVER_NAME}.database.windows.net:1433/${SQL_DB_NAME}" \
    AZURE_STORAGE_CONNECTION_STRING="@Microsoft.KeyVault(SecretUri=https://${KEYVAULT_NAME}.vault.azure.net/secrets/StorageConnectionString/)" \
    AZURE_STORAGE_CONTAINER_NAME=$CONTAINER_NAME \
    USE_AZURE_STORAGE=true \
    APPLICATIONINSIGHTS_CONNECTION_STRING="@Microsoft.KeyVault(SecretUri=https://${KEYVAULT_NAME}.vault.azure.net/secrets/AppInsightsConnectionString/)" \
    APPLICATIONINSIGHTS_ROLE_NAME=clarifai-webapp \
    AZURE_KEY_VAULT_URL="https://${KEYVAULT_NAME}.vault.azure.net/" \
    WEBSITE_MOUNT_ENABLED=1 \
    LOG_TO_STDOUT=true \
    SSL_REDIRECT=true

# 启用Web App的托管身份
echo "Enabling Managed Identity for Web App..."
az webapp identity assign \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP

# 获取托管身份的对象ID
APP_OBJECTID=$(az webapp identity show \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query principalId \
    --output tsv)

# 授权Web App访问Key Vault
echo "Granting Web App access to Key Vault..."
az keyvault set-policy \
    --name $KEYVAULT_NAME \
    --resource-group $RESOURCE_GROUP \
    --object-id $APP_OBJECTID \
    --secret-permissions get list

echo "Deployment setup complete! Now you can deploy your code using the following command:"
echo "az webapp deployment source config-zip --resource-group $RESOURCE_GROUP --name $APP_NAME --src clarifai_app.zip"
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