#!/usr/bin/env python
import os
from app import create_app

# 从环境变量中获取配置，默认为development
config_name = os.environ.get('FLASK_ENV', 'development')
app = create_app(config_name)

if __name__ == '__main__':
    # 从环境变量中获取端口，默认为5000
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 