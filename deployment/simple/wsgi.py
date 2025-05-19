#!/usr/bin/env python
import sys
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

try:
    logger.info("正在加载应用...")
    from simple_app import app as application
    logger.info("应用加载成功")
except Exception as e:
    logger.error(f"应用加载失败: {str(e)}")
    raise

# 这个变量'application'是由WSGI服务器寻找的
# 确保变量名为'application' 