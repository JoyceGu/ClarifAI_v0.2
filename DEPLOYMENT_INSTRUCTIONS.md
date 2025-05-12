# ClarifAI 部署指南

本文档提供了详细的ClarifAI应用部署到Azure的步骤说明。

## 修复本地开发问题

您在本地运行应用时遇到的`ModuleNotFoundError: No module named 'psycopg2'`错误已解决。这是由于.env文件中配置了PostgreSQL数据库连接，但本地环境中没有正确设置PostgreSQL。

### 开发环境配置

在本地开发时，请确保：

1. **清除或修改DATABASE_URL环境变量**
   ```bash
   # 运行应用时清除数据库URL，使用SQLite
   export DATABASE_URL="" && export FLASK_ENV=development && flask run --port=8000
   ```

2. **或者创建.env.development文件**
   ```
   # Flask应用配置 - 开发环境
   FLASK_ENV=development
   # 注释掉DATABASE_URL以使用SQLite
   # DATABASE_URL=postgresql://...
   ```

## Azure部署流程

我们已经优化了部署流程，以解决构建缓慢的问题。以下是完整部署步骤：

### 1. 部署前准备

1. **确保已安装和配置Azure CLI**
   ```bash
   az --version
   az login
   ```

2. **创建生产环境配置文件**
   创建.env.production文件，包含以下内容：
   ```
   # Flask应用配置 - 生产环境
   FLASK_ENV=production
   DATABASE_URL=mssql+pymssql://username:password@server.database.windows.net:1433/dbname
   USE_AZURE_STORAGE=true
   # ...其他Azure配置...
   ```

### 2. 创建Azure资源

运行优化后的部署脚本创建所需的Azure资源：

```bash
./deploy_to_azure.sh
```

请记下脚本输出的资源名称和信息，包括：
- Resource Group
- App Name
- SQL Server
- Storage Account
- App Service URL

### 3. 创建部署包

使用优化后的脚本创建部署包：

```bash
./prepare_deploy_package.sh
```

### 4. 部署应用程序

使用以下命令部署应用程序：

```bash
# 使用脚本输出中的资源组和应用名称
RESOURCE_GROUP="脚本输出的资源组名称"
APP_NAME="脚本输出的应用名称"

# 部署到生产环境
az webapp deployment source config-zip --resource-group $RESOURCE_GROUP --name $APP_NAME --src deployment/clarifai_app.zip
```

或者使用部署槽位进行零停机部署：

```bash
# 部署到过渡环境
az webapp deployment source config-zip --resource-group $RESOURCE_GROUP --name $APP_NAME --slot staging --src deployment/clarifai_app.zip

# 验证过渡环境功能正常后，交换到生产环境
az webapp deployment slot swap --resource-group $RESOURCE_GROUP --name $APP_NAME --slot staging --target-slot production
```

### 5. 配置Azure服务

1. **Azure OpenAI配置**
   ```bash
   az webapp config appsettings set \
       --name $APP_NAME \
       --resource-group $RESOURCE_GROUP \
       --settings \
       AZURE_OPENAI_API_KEY="your-api-key" \
       AZURE_OPENAI_ENDPOINT="https://your-resource-name.openai.azure.com/" \
       AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o-mini" \
       AZURE_OPENAI_API_VERSION="2025-04-15"
   ```

2. **Microsoft Entra ID配置**
   ```bash
   az webapp config appsettings set \
       --name $APP_NAME \
       --resource-group $RESOURCE_GROUP \
       --settings \
       ENTRA_CLIENT_ID="your-client-id" \
       ENTRA_CLIENT_SECRET="your-client-secret" \
       ENTRA_TENANT_ID="your-tenant-id" \
       ENTRA_REDIRECT_PATH="/auth/callback"
   ```

### 6. 监控部署

使用以下命令查看部署日志和状态：

```bash
# 查看部署状态
az webapp deployment list --name $APP_NAME --resource-group $RESOURCE_GROUP

# 查看应用程序日志
az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP
```

### 7. 访问应用程序

部署完成后，您可以通过以下URL访问应用程序：

```
https://<app-name>.azurewebsites.net
```

## 部署优化总结

为解决部署缓慢的问题，我们进行了以下优化：

1. **减小部署包大小**
   - 创建了.deployignore文件排除不必要的文件
   - 使用rsync过滤不需要的文件

2. **优化构建过程**
   - 创建了.deployment文件配置构建参数
   - 设置了SCM_DO_BUILD_DURING_DEPLOYMENT=true
   - 添加了构建优化配置

3. **提升App Service性能**
   - 将App Service Plan从F1免费层升级到B1 Basic层
   - 启用了本地缓存功能
   - 创建了部署槽位实现零停机部署

4. **改进部署和启动脚本**
   - 优化了启动脚本，添加了日志记录
   - 添加了环境检测，自动适应不同环境

如需更多部署信息，请参考README.md中的"Azure Deployment Guide"和"Deployment Optimization"部分。 