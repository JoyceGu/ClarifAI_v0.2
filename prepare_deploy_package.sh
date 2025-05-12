#!/bin/bash
# 准备Azure部署包 - 优化版本

echo "======== 准备优化的Azure部署包 ========"

# 确保目录存在
mkdir -p deployment

# 清理旧文件
if [ -f "deployment/clarifai_app.zip" ]; then
    echo "正在删除旧的部署包..."
    rm deployment/clarifai_app.zip
fi

# 创建临时部署目录
echo "正在准备部署文件..."
TEMP_DIR="deployment/temp"
mkdir -p $TEMP_DIR

# 使用rsync排除.deployignore中列出的文件
if [ -f ".deployignore" ]; then
    echo "使用.deployignore排除不必要的文件..."
    rsync -av --exclude-from='.deployignore' . $TEMP_DIR/
else
    # 如果没有.deployignore文件，使用基本复制
    echo "警告: 未找到.deployignore文件，仅复制基本文件..."
    cp -r app $TEMP_DIR/
    cp -r migrations $TEMP_DIR/
    cp requirements.txt $TEMP_DIR/
    cp config.py $TEMP_DIR/
    cp run.py $TEMP_DIR/
    cp web.config $TEMP_DIR/
    cp .env.example $TEMP_DIR/.env.example
fi

# 创建精简版requirements.txt以加快部署速度
echo "创建优化的requirements.txt..."
if command -v pip-compile &> /dev/null; then
    echo "# 自动生成的优化依赖文件" > $TEMP_DIR/requirements-optimized.txt
    pip-compile requirements.txt --output-file=- | grep -v '^#' | grep -v '^-e' >> $TEMP_DIR/requirements-optimized.txt
    # 替换原始的requirements.txt
    mv $TEMP_DIR/requirements-optimized.txt $TEMP_DIR/requirements.txt
else
    echo "警告: pip-compile未安装，跳过依赖优化"
fi

# 创建.deployment文件以优化部署过程
cat > $TEMP_DIR/.deployment << 'EOF'
[config]
SCM_DO_BUILD_DURING_DEPLOYMENT=true
command = bash ./startup.sh
EOF

# 创建优化的启动脚本
cat > $TEMP_DIR/startup.sh << 'EOF'
#!/bin/bash
# 部署后初始化脚本 - 优化版本

# 设置日志文件
LOG_FILE="startup_log.txt"
exec > >(tee -a $LOG_FILE) 2>&1

echo "=============== 开始部署初始化 [$(date)] ==============="

# 初始化环境
export FLASK_APP=run.py
export FLASK_ENV=production

# 设置Azure App Service环境变量，避免重复进行缓慢的Python构建过程
export SCM_DO_BUILD_DURING_DEPLOYMENT=true

echo "正在初始化数据库..."
flask db upgrade

# 创建初始测试用户（如果不存在）
python << 'PYTHON_SCRIPT'
from app import create_app, db
from app.models.user import User, UserRole
from werkzeug.security import generate_password_hash

app = create_app('production')
with app.app_context():
    # 检查是否已有用户
    if User.query.count() == 0:
        # 创建PM用户
        pm_user = User(
            email='pm@test.com',
            username='Product Manager',
            role=UserRole.PM
        )
        pm_user.password_hash = generate_password_hash('password123')
        
        # 创建研究员用户
        researcher_user = User(
            email='researcher@test.com',
            username='Researcher',
            role=UserRole.RESEARCHER
        )
        researcher_user.password_hash = generate_password_hash('password123')
        
        db.session.add(pm_user)
        db.session.add(researcher_user)
        db.session.commit()
        print("已创建初始测试用户")
    else:
        print("已存在用户，跳过初始用户创建")
PYTHON_SCRIPT

# 使应用正确加载Azure配置
echo "正在优化Azure服务连接配置..."
if [ -n "$WEBSITE_SITE_NAME" ]; then  # 检查是否在Azure环境中
    echo "在Azure环境中运行，启用应用缓存..."
    touch .skip-lock  # 避免每次都重新构建
    
    # 创建web.debug.config
    if [ ! -f "web.debug.config" ]; then
        cp web.config web.debug.config
    fi
fi

echo "=============== 初始化完成 [$(date)] ==============="
EOF

# 使脚本可执行
chmod +x $TEMP_DIR/startup.sh

# 创建zip文件
echo "正在创建优化的部署包..."
cd $TEMP_DIR
zip -r ../clarifai_app.zip ./* .deployment
cd ../..

# 计算部署包大小
PACKAGE_SIZE=$(du -h deployment/clarifai_app.zip | cut -f1)

# 清理临时文件
echo "正在清理临时文件..."
rm -rf $TEMP_DIR

echo "部署包已创建: $(pwd)/deployment/clarifai_app.zip (大小: $PACKAGE_SIZE)"
echo "完成 ✓" 