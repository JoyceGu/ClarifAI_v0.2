# ClarifAI - 智能任务管理平台

ClarifAI是一个基于Python Flask的任务管理平台，集成了Azure OpenAI能力，提供任务提交、验证、分配和跟踪功能。

## 核心功能

1. **用户认证系统**
   - 登录/注册
   - 与Microsoft Entra ID集成（计划中）

2. **任务管理**
   - 提交新任务/需求
   - 分配任务给团队成员
   - 追踪分配给自己的任务
   - 任务历史记录查看

3. **智能任务验证**
   - 使用Azure OpenAI验证任务的清晰度/可行性
   - 检查是否存在类似案例（通过知识库API）

4. **文件管理**
   - 文件上传/存储空间
   - 文件探索和管理界面

## 技术栈

- **后端**: Python Flask
- **前端**: HTML, CSS, JavaScript (Bootstrap)
- **数据库**: SQLite (开发), PostgreSQL (生产)
- **认证**: Flask-Login (本地), Microsoft Entra ID (Azure部署)
- **AI集成**: Azure OpenAI
- **云部署**: Azure App Service

## 安装说明

1. 克隆代码库

```bash
git clone [repository-url]
cd ClarifAI_v0.2
```

2. 创建并激活虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # MacOS/Linux
# 或者
venv\Scripts\activate  # Windows
```

3. 安装依赖

```bash
pip install -r requirements.txt
```

4. 初始化数据库

```bash
flask db init
flask db migrate
flask db upgrade
```

5. 运行应用

```bash
flask run --port=8000
```

6. 在浏览器中访问应用

```
http://localhost:8000
```

## 项目结构

```
ClarifAI/
├── app/
│   ├── __init__.py
│   ├── models/
│   ├── routes/
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   ├── templates/
│   └── utils/
├── migrations/
├── instance/
├── venv/
├── .gitignore
├── config.py
├── requirements.txt
└── README.md
```

## Azure部署指南

### 前提条件

1. Azure账户
2. 已安装Azure CLI
3. 本地已配置的项目

### 部署步骤

#### 1. 配置Azure服务

运行提供的部署脚本，创建所需Azure资源：

```bash
# 确保脚本有执行权限
chmod +x deploy_to_azure.sh
# 运行部署脚本
./deploy_to_azure.sh
```

这个脚本会自动创建以下Azure资源：
- 资源组
- Azure SQL Server和数据库
- Azure Blob Storage
- Application Insights
- Azure Key Vault
- App Service Plan
- Web App

#### 2. 准备部署包

运行以下命令创建部署包：

```bash
# 确保脚本有执行权限
chmod +x prepare_deploy_package.sh
# 创建部署包
./prepare_deploy_package.sh
```

#### 3. 部署应用程序

```bash
# 替换为您的资源组和应用名称
RESOURCE_GROUP="clarifai-resources"
APP_NAME="clarifai-app"

# 部署到Azure
az webapp deployment source config-zip --resource-group $RESOURCE_GROUP --name $APP_NAME --src deployment/clarifai_app.zip
```

#### 4. 配置Azure OpenAI和Microsoft Entra ID

1. **Azure OpenAI配置**

   在Azure Portal中创建Azure OpenAI资源，然后更新应用设置：
   
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

   在Azure Portal的Entra ID中注册新应用，然后更新应用设置：
   
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

#### 5. 完成部署

部署完成后，您可以访问Azure Web App URL查看您的应用：

```
https://clarifai-app.azurewebsites.net
```

#### 6. 部署后操作

1. 运行数据库迁移（这在启动脚本中已自动执行）
2. 通过Azure Portal监控应用性能

### 故障排除

1. **查看应用日志**：
   ```bash
   az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP
   ```

2. **检查部署状态**：
   ```bash
   az webapp deployment list --name $APP_NAME --resource-group $RESOURCE_GROUP
   ```

3. **重启应用**：
   ```bash
   az webapp restart --name $APP_NAME --resource-group $RESOURCE_GROUP
   ```

## 开发路线图

1. 基础功能实现（认证、任务管理、文件上传）
2. Azure OpenAI集成
3. Microsoft Entra ID集成
4. 知识库API集成
5. Azure部署配置

## 测试账号

- PM: pm@test.com / password123
- Researcher: researcher@test.com / password123

## 故障排除

### 常见问题及解决方案

#### 1. Azure连接字符串错误
**问题**: 启动时出现 "Invalid connection string" 错误
```
ValueError: Invalid connection string
```

**解决方案**: 
- 确保.env文件中的Azure服务连接字符串是有效的，或者将其注释掉
- 对于本地开发环境，可以将以下配置注释掉：
  ```bash
  #APPLICATIONINSIGHTS_CONNECTION_STRING=
  #AZURE_KEY_VAULT_URL=
  ```

#### 2. 端口被占用
**问题**: 启动时提示"Address already in use"
```
Port 8000 is in use by another program
```

**解决方案**:
```bash
# 查找占用端口的进程
lsof -i :8000
# 终止进程（将PID替换为实际的进程ID）
kill <PID>
```

#### 3. Python命令未找到
**问题**: 运行python命令时提示"command not found"

**解决方案**:
- 确保虚拟环境已激活
- 在macOS上使用python3代替python：
  ```bash
  python3 app.py
  ```

#### 4. 依赖包安装失败
**问题**: pip install失败或包版本冲突

**解决方案**:
```bash
# 升级pip
pip install --upgrade pip
# 清理缓存并重新安装
pip cache purge
pip install -r requirements.txt --force-reinstall
```

#### 5. 数据库初始化问题
**问题**: 数据库相关错误

**解决方案**:
```bash
# 初始化数据库
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# 创建初始用户
flask init-db
```

#### 6. GitHub push被阻止 - 检测到敏感信息
**问题**: push时出现"Repository rule violations found"错误
```
Push cannot contain secrets - Azure OpenAI Key
```

**解决方案**:
```bash
# 方法1: 删除包含敏感信息的文件
rm .env.backup  # 或其他包含密钥的文件

# 方法2: 如果敏感信息在Git历史中，需要重写历史
git filter-branch --force --index-filter 'git rm --cached --ignore-unmatch .env.backup' --prune-empty --tag-name-filter cat -- --all

# 强制push（注意：这会重写远程历史）
git push origin branch-name --force
```

#### 7. Azure部署认证失败
**问题**: push到Azure时出现"Authentication failed"

**解决方案**:
```bash
# 获取Azure部署凭据
az webapp deployment list-publishing-profiles --name your-app-name --resource-group your-resource-group

# 或者使用Azure CLI登录
az login

# 设置部署用户
az webapp deployment user set --user-name your-username --password your-password
```

#### 8. Gunicorn命令未找到
**问题**: 运行gunicorn时提示"command not found"

**解决方案**:
```bash
# 确保虚拟环境已激活
source venv/bin/activate

# 重新安装gunicorn
pip install gunicorn==21.2.0

# 验证安装
gunicorn --version
```

### 开发环境配置

确保您的.env文件包含以下最小配置：
```bash
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///instance/clarifai.db
UPLOAD_FOLDER=app/static/uploads
MAX_CONTENT_LENGTH=16777216
USE_AZURE_STORAGE=false
LOG_TO_STDOUT=false
```

### 启动应用的正确步骤

1. **激活虚拟环境**:
   ```bash
   source venv/bin/activate  # macOS/Linux
   ```

2. **安装依赖**:
   ```bash
   pip install -r requirements.txt
   ```

3. **配置环境变量**:
   - 复制 `env.example` 到 `.env`
   - 根据需要修改配置

4. **启动应用**:
   ```bash
   python3 app.py
   ```

5. **访问应用**:
   打开浏览器访问 `http://localhost:8000`