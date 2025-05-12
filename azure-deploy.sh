#!/bin/bash
# Azure部署脚本 - ClarifAI应用程序部署到Azure

# 输出颜色设置
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # 重置颜色

# 配置变量 - 根据需要修改
export RESOURCE_GROUP="clarifai-rg"
export LOCATION="eastus"
export APP_NAME="clarifai-app"
export DATABASE_SERVER="clarifai-db-server"
export DATABASE_NAME="clarifaidb"
export DATABASE_USERNAME="clarifaiadmin"
export DATABASE_PASSWORD="P@ssw0rd$(date +%s)"  # 生成随机密码
export STORAGE_ACCOUNT="clarifaistorage$(date +%s | tail -c 6)"  # 确保唯一性
export CONTAINER_NAME="fileuploads"
export INSIGHTS_NAME="clarifai-insights"
export KEYVAULT_NAME="clarifai-keyvault"
export OPENAI_NAME="clarifai-openai"
export OPENAI_DEPLOYMENT="gpt-4o-mini"

# 输出配置信息
echo -e "${GREEN}开始部署ClarifAI应用到Azure...${NC}"
echo ""
echo -e "${YELLOW}使用以下配置:${NC}"
echo "资源组: $RESOURCE_GROUP"
echo "位置: $LOCATION"
echo "应用名称: $APP_NAME"
echo "数据库服务器: $DATABASE_SERVER"
echo "数据库名: $DATABASE_NAME"
echo "存储账户: $STORAGE_ACCOUNT"
echo "Application Insights: $INSIGHTS_NAME"
echo "Key Vault: $KEYVAULT_NAME"
echo -e "Azure OpenAI: $OPENAI_NAME\n"

# 确认继续
read -p "继续部署? (y/n): " confirm
if [[ $confirm != "y" && $confirm != "Y" ]]; then
  echo -e "${RED}部署已取消${NC}"
  exit 1
fi

# 检查Azure CLI是否已登录
echo -e "\n${YELLOW}检查Azure CLI登录状态...${NC}"
az account show > /dev/null 2>&1
if [ $? -ne 0 ]; then
  echo -e "${RED}未登录Azure CLI，请先运行 'az login'${NC}"
  exit 1
fi

# 1. 创建资源组
echo -e "\n${YELLOW}创建资源组...${NC}"
az group create --name $RESOURCE_GROUP --location $LOCATION

# 2. 创建存储账户和容器
echo -e "\n${YELLOW}创建Azure Storage...${NC}"
az storage account create \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS

# 获取存储账户连接字符串
STORAGE_CONNECTION_STRING=$(az storage account show-connection-string \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --output tsv)

# 创建存储容器
az storage container create \
  --name $CONTAINER_NAME \
  --account-name $STORAGE_ACCOUNT \
  --public-access blob \
  --connection-string "$STORAGE_CONNECTION_STRING"

# 3. 创建PostgreSQL服务器和数据库
echo -e "\n${YELLOW}创建Azure PostgreSQL服务器和数据库...${NC}"
az postgres server create \
  --name $DATABASE_SERVER \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --admin-user $DATABASE_USERNAME \
  --admin-password $DATABASE_PASSWORD \
  --sku-name B_Gen5_1

# 配置PostgreSQL服务器防火墙规则 - 允许Azure服务访问
az postgres server firewall-rule create \
  --resource-group $RESOURCE_GROUP \
  --server $DATABASE_SERVER \
  --name AllowAllAzureIPs \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0

# 创建数据库
az postgres db create \
  --resource-group $RESOURCE_GROUP \
  --server-name $DATABASE_SERVER \
  --name $DATABASE_NAME

# 获取数据库连接字符串
DATABASE_URL="postgresql://${DATABASE_USERNAME}:${DATABASE_PASSWORD}@${DATABASE_SERVER}.postgres.database.azure.com/${DATABASE_NAME}"

# 4. 创建Application Insights
echo -e "\n${YELLOW}创建Application Insights...${NC}"
az monitor app-insights component create \
  --app $INSIGHTS_NAME \
  --location $LOCATION \
  --resource-group $RESOURCE_GROUP

# 获取Application Insights连接字符串
INSIGHTS_CONNECTION_STRING=$(az monitor app-insights component show \
  --app $INSIGHTS_NAME \
  --resource-group $RESOURCE_GROUP \
  --query connectionString \
  --output tsv)

# 5. 创建Key Vault并存储机密
echo -e "\n${YELLOW}创建Azure Key Vault...${NC}"
az keyvault create \
  --name $KEYVAULT_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

# 生成随机SECRET_KEY
SECRET_KEY=$(openssl rand -hex 32)

# 将机密存储到Key Vault
az keyvault secret set --vault-name $KEYVAULT_NAME --name "DATABASE-URL" --value "$DATABASE_URL"
az keyvault secret set --vault-name $KEYVAULT_NAME --name "STORAGE-CONNECTION-STRING" --value "$STORAGE_CONNECTION_STRING"
az keyvault secret set --vault-name $KEYVAULT_NAME --name "APPLICATIONINSIGHTS-CONNECTION-STRING" --value "$INSIGHTS_CONNECTION_STRING"
az keyvault secret set --vault-name $KEYVAULT_NAME --name "SECRET-KEY" --value "$SECRET_KEY"

# 6. 创建Azure App Service计划和Web应用
echo -e "\n${YELLOW}创建App Service计划和Web应用...${NC}"
az appservice plan create \
  --name ${APP_NAME}-plan \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku B1 \
  --is-linux

# 创建Web应用
az webapp create \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --plan ${APP_NAME}-plan \
  --runtime "PYTHON:3.10"

# 配置Web应用设置
az webapp config set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --startup-file "gunicorn -w 4 -k gthread -t 60 'app:create_app()'"

# 添加Web应用配置
az webapp config appsettings set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings \
    DATABASE_URL="$DATABASE_URL" \
    AZURE_STORAGE_CONNECTION_STRING="$STORAGE_CONNECTION_STRING" \
    AZURE_STORAGE_CONTAINER_NAME="$CONTAINER_NAME" \
    APPLICATIONINSIGHTS_CONNECTION_STRING="$INSIGHTS_CONNECTION_STRING" \
    SECRET_KEY="$SECRET_KEY" \
    FLASK_ENV=production \
    AZURE_KEY_VAULT_URL="https://${KEYVAULT_NAME}.vault.azure.net/" \
    LOG_TO_STDOUT=true \
    APPLICATIONINSIGHTS_ROLE_NAME="webapp" \
    AZURE_OPENAI_DEPLOYMENT_NAME="$OPENAI_DEPLOYMENT"

# 7. 为App Service启用Key Vault引用
# 首先获取App Service的系统分配身份
az webapp identity assign \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP

# 获取分配的身份ID
WEBAPP_IDENTITY=$(az webapp identity show \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query principalId \
  --output tsv)

# 授予Web应用访问Key Vault的权限
az keyvault set-policy \
  --name $KEYVAULT_NAME \
  --object-id $WEBAPP_IDENTITY \
  --secret-permissions get list

# 8. 提示手动设置Microsoft Entra ID集成
echo -e "\n${YELLOW}Microsoft Entra ID集成需要手动配置:${NC}"
echo "1. 在Azure Portal中注册新应用程序"
echo "2. 配置重定向URI: https://${APP_NAME}.azurewebsites.net/auth/callback"
echo "3. 创建客户端密钥"
echo "4. 获取应用程序ID和目录ID"
echo "5. 配置Web应用的以下设置:"
echo "   - ENTRA_CLIENT_ID"
echo "   - ENTRA_CLIENT_SECRET"
echo "   - ENTRA_TENANT_ID"

# 9. 部署指南
echo -e "\n${GREEN}部署信息:${NC}"
echo "部署完成后，您需要:"
echo "1. 使用Git或ZIP部署代码到App Service:"
echo "   az webapp deployment source config-local-git --name $APP_NAME --resource-group $RESOURCE_GROUP"
echo "2. 运行数据库迁移:"
echo "   - 连接到App Service的SSH控制台"
echo "   - 运行: flask db upgrade"
echo "3. 初始化测试用户:"
echo "   - 运行: python init_users.py"
echo ""
echo -e "${GREEN}部署已完成!${NC}"
echo "Web应用URL: https://${APP_NAME}.azurewebsites.net" 