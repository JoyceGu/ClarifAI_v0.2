#!/usr/bin/env python3

import sqlite3
import os
from werkzeug.security import generate_password_hash

# 确保instance目录存在
os.makedirs('instance', exist_ok=True)

# 数据库文件路径
db_path = os.path.join(os.path.abspath('.'), 'instance', 'clarifai.db')

print(f"数据库路径: {db_path}")

try:
    # 删除现有数据库文件
    if os.path.exists(db_path):
        os.remove(db_path)
        print("已删除现有数据库文件")
    
    # 创建数据库连接
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 创建用户表
    cursor.execute('''
        CREATE TABLE user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email VARCHAR(120) UNIQUE NOT NULL,
            username VARCHAR(80),
            password_hash VARCHAR(128),
            role VARCHAR(20) DEFAULT 'RESEARCHER',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_entra_user BOOLEAN DEFAULT 0,
            entra_user_id VARCHAR(128) UNIQUE
        )
    ''')
    
    # 创建任务表
    cursor.execute('''
        CREATE TABLE task (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title VARCHAR(200) NOT NULL,
            business_goal TEXT,
            priority VARCHAR(20) NOT NULL DEFAULT 'medium',
            status VARCHAR(20) NOT NULL DEFAULT 'draft',
            output_type VARCHAR(20) NOT NULL DEFAULT 'report',
            creator_id INTEGER NOT NULL,
            assignee_id INTEGER,
            deadline DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            verification_result TEXT,
            FOREIGN KEY (creator_id) REFERENCES user (id),
            FOREIGN KEY (assignee_id) REFERENCES user (id)
        )
    ''')
    
    # 创建文件表
    cursor.execute('''
        CREATE TABLE file (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename VARCHAR(200) NOT NULL,
            original_filename VARCHAR(200) NOT NULL,
            file_path VARCHAR(500) NOT NULL,
            file_size INTEGER NOT NULL,
            file_type VARCHAR(100) NOT NULL,
            uploader_id INTEGER NOT NULL,
            task_id INTEGER,
            upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_blob BOOLEAN DEFAULT 0,
            blob_url VARCHAR(500),
            FOREIGN KEY (uploader_id) REFERENCES user (id),
            FOREIGN KEY (task_id) REFERENCES task (id)
        )
    ''')
    
    print("数据库表创建成功")
    
    # 创建测试用户
    pm_password_hash = generate_password_hash('password123')
    researcher_password_hash = generate_password_hash('password123')
    
    cursor.execute('''
        INSERT INTO user (email, username, password_hash, role)
        VALUES (?, ?, ?, ?)
    ''', ('pm@test.com', 'PM', pm_password_hash, 'RESEARCHER'))
    
    cursor.execute('''
        INSERT INTO user (email, username, password_hash, role)
        VALUES (?, ?, ?, ?)
    ''', ('researcher@test.com', 'Researcher', researcher_password_hash, 'RESEARCHER'))
    
    # 提交更改
    conn.commit()
    print("测试用户创建成功")
    
    # 验证数据
    cursor.execute('SELECT id, email, username FROM user')
    users = cursor.fetchall()
    print(f"数据库中的用户:")
    for user in users:
        print(f"  ID: {user[0]}, Email: {user[1]}, Username: {user[2]}")
    
    cursor.close()
    conn.close()
    print("数据库初始化完成!")
    
except Exception as e:
    print(f"初始化失败: {e}")
    import traceback
    traceback.print_exc() 