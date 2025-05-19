#!/usr/bin/env python
import os
import sys
import logging

# 配置基本日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

logger.info("Starting application initialization...")

try:
    from app import create_app
    
    # 从环境变量中获取配置，默认为production
    config_name = os.environ.get('FLASK_ENV', 'production')
    logger.info(f"Using configuration: {config_name}")
    
    app = create_app(config_name)
    logger.info("Application created successfully")
    
    if __name__ == '__main__':
        # 从环境变量中获取端口，默认为5000
        port = int(os.environ.get('PORT', 5000))
        logger.info(f"Starting Flask development server on port {port}")
        app.run(host='0.0.0.0', port=port)
except Exception as e:
    logger.error(f"Error initializing application: {str(e)}", exc_info=True)
    raise 