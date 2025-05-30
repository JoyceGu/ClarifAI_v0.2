#!/bin/bash

# ClarifAI 应用启动脚本
# 设置数据库URL环境变量来避免中文路径问题

echo "启动 ClarifAI 应用..."

# 确保临时数据库目录存在
mkdir -p /tmp/clarifai_db

# 如果临时目录中没有数据库文件，从项目目录复制
if [ ! -f "/tmp/clarifai_db/clarifai.db" ]; then
    if [ -f "instance/clarifai.db" ]; then
        echo "复制数据库文件到临时目录..."
        cp instance/clarifai.db /tmp/clarifai_db/
    else
        echo "数据库文件不存在，请先运行: python simple_init.py"
        exit 1
    fi
fi

# 设置环境变量并启动应用
export DATABASE_URL="sqlite:////tmp/clarifai_db/clarifai.db"
echo "数据库URL: $DATABASE_URL"
echo "应用将在 http://localhost:8000 启动"
echo "测试账号:"
echo "  PM: pm@test.com / password123"
echo "  Researcher: researcher@test.com / password123"
echo ""
echo "按 Ctrl+C 停止应用"

python app.py 