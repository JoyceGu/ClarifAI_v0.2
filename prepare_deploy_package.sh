#!/bin/bash
# 准备Azure部署包

# 确保目录存在
mkdir -p deployment

# 清理旧文件
if [ -f "deployment/clarifai_app.zip" ]; then
    rm deployment/clarifai_app.zip
fi

# 复制所有需要的文件到临时目录
echo "正在准备部署文件..."
mkdir -p deployment/temp
cp -r app deployment/temp/
cp -r migrations deployment/temp/
cp requirements.txt deployment/temp/
cp config.py deployment/temp/
cp run.py deployment/temp/
cp web.config deployment/temp/
cp .env.example deployment/temp/.env.example

# 创建初始化脚本
cat > deployment/temp/startup.sh << 'EOF'
#!/bin/bash
# 部署后初始化脚本

# 初始化数据库
echo "正在初始化数据库..."
export FLASK_APP=run.py
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

echo "初始化完成！"
EOF

# 使脚本可执行
chmod +x deployment/temp/startup.sh

# 创建zip文件
echo "正在创建部署包..."
cd deployment/temp
zip -r ../clarifai_app.zip ./*
cd ../..

# 清理临时文件
rm -rf deployment/temp

echo "部署包已创建: $(pwd)/deployment/clarifai_app.zip" 