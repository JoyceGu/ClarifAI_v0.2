#!/usr/bin/env python3

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 确保数据库文件夹存在
os.makedirs('instance', exist_ok=True)

from app import create_app, db
from app.models import User, UserRole

def init_database():
    # 创建应用
    app = create_app()
    
    with app.app_context():
        try:
            # 删除所有表
            db.drop_all()
            print("已删除现有表")
            
            # 创建所有表
            db.create_all()
            print("数据库表创建成功")
            
            # 创建测试用户
            pm_user = User(
                email='pm@test.com',
                password='password123',
                role=UserRole.RESEARCHER,
                username='PM'
            )
            
            researcher_user = User(
                email='researcher@test.com',
                password='password123',
                role=UserRole.RESEARCHER,
                username='Researcher'
            )
            
            # 添加到数据库
            db.session.add(pm_user)
            db.session.add(researcher_user)
            db.session.commit()
            
            print("测试用户创建成功!")
            
            # 验证用户
            users = User.query.all()
            print(f"数据库中共有 {len(users)} 个用户:")
            for user in users:
                print(f"  - {user.email} ({user.username})")
                
        except Exception as e:
            print(f"初始化失败: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    init_database() 