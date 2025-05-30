#!/usr/bin/env python3

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User

def check_database():
    app = create_app()
    
    with app.app_context():
        try:
            # 检查数据库连接
            print("正在检查数据库连接...")
            
            # 查询所有用户
            users = User.query.all()
            print(f"数据库中共有 {len(users)} 个用户")
            
            for user in users:
                print(f"用户: {user.email}, 用户名: {user.username}, 有密码: {bool(user.password_hash)}")
                
                # 测试密码验证
                if user.email in ['pm@test.com', 'researcher@test.com']:
                    password_ok = user.check_password('password123')
                    print(f"  密码验证结果: {password_ok}")
                    
            # 如果没有用户，创建测试用户
            if len(users) == 0:
                print("数据库为空，正在创建测试用户...")
                from app.models import UserRole
                
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
                
                db.session.add(pm_user)
                db.session.add(researcher_user)
                db.session.commit()
                
                print("测试用户创建成功!")
                
        except Exception as e:
            print(f"数据库错误: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    check_database() 