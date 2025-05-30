# ClarifAI - 数据分析需求管理平台

ClarifAI 是一个专为数据分析团队设计的需求管理平台，帮助产品经理和数据分析师更好地协作，管理数据分析任务和需求。

## 主要功能

### 核心功能
- **需求提交与管理**: 产品经理可以提交详细的数据分析需求
- **任务分配**: 支持将任务分配给特定的数据分析师
- **进度跟踪**: 实时跟踪任务状态和进度
- **文件管理**: 支持上传和管理相关的数据文件和文档
- **优先级管理**: 支持设置和管理任务优先级

### 技术特性
- **现代化界面**: 基于Bootstrap 5的响应式设计
- **身份验证**: 支持本地用户认证和Microsoft Entra ID集成
- **文件存储**: 支持本地文件存储和Azure Blob Storage
- **数据库**: 使用SQLite数据库，易于部署和维护
- **RESTful API**: 提供完整的API接口

## 快速开始

### 环境要求
- Python 3.9+
- Flask 2.0+
- SQLAlchemy
- 其他依赖见 `requirements.txt`

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd ClarifAI_v0.2
```

2. **创建虚拟环境**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **初始化数据库**
```bash
python simple_init.py
```

5. **启动应用**
```bash
# 推荐使用启动脚本（自动处理数据库路径问题）
./start_app.sh

# 或者手动设置环境变量
DATABASE_URL="sqlite:////tmp/clarifai_db/clarifai.db" python app.py
```

6. **访问应用**
打开浏览器访问: http://localhost:8000

### 测试账号
- **PM账号**: pm@test.com / password123
- **Researcher账号**: researcher@test.com / password123

## 重要说明

### 数据库路径问题
由于项目路径包含中文字符，SQLAlchemy可能无法正确访问数据库文件。我们提供了以下解决方案：

1. **使用启动脚本**: `./start_app.sh` (推荐)
2. **手动设置环境变量**: 
   ```bash
   export DATABASE_URL="sqlite:////tmp/clarifai_db/clarifai.db"
   python app.py
   ```

数据库文件会自动复制到 `/tmp/clarifai_db/` 目录中，避免中文路径问题。

## 项目结构

```
ClarifAI_v0.2/
├── app/                    # 应用主目录
│   ├── __init__.py        # 应用初始化
│   ├── models/            # 数据模型
│   │   ├── __init__.py
│   │   ├── user.py        # 用户模型
│   │   ├── task.py        # 任务模型
│   │   └── file.py        # 文件模型
│   ├── routes/            # 路由处理
│   │   ├── auth.py        # 认证路由
│   │   ├── main.py        # 主页路由
│   │   ├── tasks.py       # 任务路由
│   │   ├── files.py       # 文件路由
│   │   └── errors.py      # 错误处理
│   ├── templates/         # HTML模板
│   ├── static/           # 静态资源
│   └── utils/            # 工具函数
├── instance/             # 实例配置和数据库
├── migrations/           # 数据库迁移文件
├── config.py            # 配置文件
├── app.py              # 应用入口
├── simple_init.py      # 数据库初始化脚本
├── start_app.sh        # 应用启动脚本
├── requirements.txt    # Python依赖
└── README.md          # 项目文档
```

## 配置说明

### 基础配置
应用支持多种环境配置：
- `development`: 开发环境（默认）
- `testing`: 测试环境
- `production`: 生产环境

### 环境变量
- `FLASK_CONFIG`: 指定配置环境
- `DATABASE_URL`: 数据库连接URL
- `SECRET_KEY`: Flask密钥
- `AZURE_*`: Azure服务配置（可选）
- `ENTRA_*`: Microsoft Entra ID配置（可选）

### Azure集成（可选）
应用支持与Azure服务集成：
- **Azure Blob Storage**: 文件存储
- **Azure Application Insights**: 应用监控
- **Azure Key Vault**: 密钥管理
- **Microsoft Entra ID**: 身份认证

## API文档

### 认证端点
- `GET /auth/login` - 登录页面
- `POST /auth/login` - 用户登录
- `GET /auth/logout` - 用户登出
- `GET /auth/callback` - Microsoft认证回调

### 任务管理
- `GET /tasks` - 任务列表
- `GET /tasks/create` - 创建任务页面
- `POST /tasks/create` - 提交新任务
- `GET /tasks/<id>` - 查看任务详情
- `POST /tasks/<id>/update` - 更新任务状态

### 文件管理
- `POST /files/upload` - 上传文件
- `GET /files/<id>` - 下载文件
- `DELETE /files/<id>` - 删除文件

## 故障排除

### 常见问题

1. **数据库连接错误**
   - 确保使用启动脚本或正确设置环境变量
   - 检查 `/tmp/clarifai_db/` 目录权限

2. **端口占用**
   ```bash
   lsof -i :8000
   kill <PID>
   ```

3. **依赖问题**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

4. **重新初始化数据库**
   ```bash
   python simple_init.py
   ```

### 日志调试
应用在开发模式下会显示详细的错误信息。生产环境可配置Azure Application Insights进行监控。

## 开发指南

### 添加新功能
1. 在相应的模块中添加模型、路由和模板
2. 更新数据库模式（如需要）
3. 添加相应的测试
4. 更新文档

### 数据库迁移
```bash
# 初始化迁移（仅首次）
flask db init

# 生成迁移文件
flask db migrate -m "描述"

# 应用迁移
flask db upgrade
```

### 测试
```bash
# 运行测试
python -m pytest tests/

# 代码覆盖率
python -m pytest --cov=app tests/
```

## 部署

### 本地部署
使用提供的启动脚本即可在本地运行。

### 生产部署
1. 设置 `FLASK_CONFIG=production`
2. 配置适当的数据库（PostgreSQL推荐）
3. 设置Azure服务（推荐）
4. 使用WSGI服务器（如Gunicorn）

### Azure部署
项目包含Azure部署配置文件，支持直接部署到Azure App Service。

## 贡献

欢迎提交Issue和Pull Request来改进项目。

## 许可证

[MIT License](LICENSE)

## 联系方式

如有问题或建议，请通过Issue联系我们。

---

**注意**: 这是一个开发版本，某些功能可能还在完善中。生产使用前请进行充分测试。