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

## 开发路线图

1. 基础功能实现（认证、任务管理、文件上传）
2. Azure OpenAI集成
3. Microsoft Entra ID集成
4. 知识库API集成
5. Azure部署配置

## 测试账号

- PM: pm@test.com / password123
- Researcher: researcher@test.com / password123 