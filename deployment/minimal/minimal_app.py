#!/usr/bin/env python
from flask import Flask, jsonify, render_template, redirect, url_for, flash, request
import logging
import os
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-testing')

# 首页路由
@app.route('/')
def home():
    logger.info("首页被访问")
    return render_template('main/dashboard.html', title="ClarifAI Dashboard")

# 健康检查端点
@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

# 环境信息端点（用于调试）
@app.route('/info')
def info():
    env_vars = {}
    for key, value in os.environ.items():
        if not key.startswith(('AZURE_', 'SECRET_', 'PASSWORD')):
            env_vars[key] = value
    
    return jsonify({
        "python_version": sys.version,
        "env_variables": env_vars,
        "app_config": {k: str(v) for k, v in app.config.items() if not k.startswith('SECRET')}
    })

# 登录页面（简化版）
@app.route('/login')
def login():
    return render_template('auth/login.html', title="Login")

# 简化的PM任务视图
@app.route('/tasks')
def tasks():
    sample_tasks = [
        {"id": 1, "title": "分析用户反馈", "status": "进行中", "created_at": "2025-05-18"},
        {"id": 2, "title": "优化推荐算法", "status": "待处理", "created_at": "2025-05-17"},
        {"id": 3, "title": "生成月度报告", "status": "已完成", "created_at": "2025-05-15"}
    ]
    return render_template('tasks/all_tasks.html', tasks=sample_tasks, title="任务列表")

# 启动应用
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    logger.info(f"启动应用，端口: {port}")
    app.run(host='0.0.0.0', port=port, debug=True) 