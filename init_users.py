from app import create_app, db
from app.models import User, UserRole

app = create_app()

with app.app_context():
    # 创建用户，都使用相同角色
    pm_user = User(
        email='pm@test.com',
        password='password123',
        role=UserRole.RESEARCHER,  # 统一使用同一角色
        username='PM'
    )
    
    researcher_user = User(
        email='researcher@test.com',
        password='password123',
        role=UserRole.RESEARCHER,  # 统一使用同一角色
        username='Researcher'
    )
    
    # 添加到数据库
    db.session.add(pm_user)
    db.session.add(researcher_user)
    db.session.commit()
    
    print('初始用户创建成功!') 