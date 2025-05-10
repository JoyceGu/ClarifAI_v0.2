from app import create_app, db
from app.models import User, Task, File, UserRole

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Task': Task, 'File': File}

# 添加初始用户的命令
@app.cli.command('init-db')
def init_db():
    """创建初始用户账号"""
    # 创建PM用户
    pm_user = User(
        email='pm@test.com',
        password='password123',
        role=UserRole.RESEARCHER,  # 所有用户使用相同角色
        username='PM'
    )
    
    # 创建研究员用户
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
    
    print('初始用户创建成功!')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True) 