from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User
from app import db, login_manager, get_entra_id_provider
from datetime import datetime
from app.utils.forms import LoginForm
from werkzeug.urls import url_parse

auth = Blueprint('auth', __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    
    # Microsoft Entra ID登录链接
    ms_login_url = None
    entra_id_provider = get_entra_id_provider()
    if entra_id_provider:
        ms_login_url = entra_id_provider.get_login_url()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('main.dashboard')
            return redirect(next_page)
        else:
            flash('无效的邮箱或密码', 'danger')
            
    # 获取测试账号
    test_accounts = [
        {'role': 'PM', 'email': 'pm@test.com', 'password': 'password123'},
        {'role': 'Researcher', 'email': 'researcher@test.com', 'password': 'password123'}
    ]
    
    return render_template('auth/login.html', form=form, test_accounts=test_accounts, ms_login_url=ms_login_url)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('您已成功登出', 'info')
    return redirect(url_for('auth.login'))

@auth.route('/entra-login')
def entra_login():
    """Microsoft Entra ID登录入口点"""
    entra_id_provider = get_entra_id_provider()
    if not entra_id_provider:
        flash('Microsoft Entra ID登录未配置', 'warning')
        return redirect(url_for('auth.login'))
        
    # 生成授权URL并重定向
    auth_url = entra_id_provider.get_login_url()
    return redirect(auth_url)

@auth.route('/callback')
def callback():
    """处理Microsoft Entra ID回调"""
    entra_id_provider = get_entra_id_provider()
    if not entra_id_provider:
        flash('Microsoft Entra ID登录未配置', 'warning')
        return redirect(url_for('auth.login'))
    
    try:
        # 验证状态以防止CSRF攻击
        if not entra_id_provider.verify_callback():
            flash('无效的认证请求', 'danger')
            return redirect(url_for('auth.login'))
        
        # 获取授权码
        auth_code = request.args.get('code')
        if not auth_code:
            flash('认证失败', 'danger')
            return redirect(url_for('auth.login'))
        
        # 获取token
        result = entra_id_provider.get_token_from_code(auth_code)
        if not result or 'access_token' not in result:
            flash('获取访问令牌失败', 'danger')
            return redirect(url_for('auth.login'))
        
        # 获取用户信息
        user_info = entra_id_provider.get_user_info(result['access_token'])
        if not user_info or 'userPrincipalName' not in user_info:
            flash('获取用户信息失败', 'danger')
            return redirect(url_for('auth.login'))
        
        # 检查用户是否存在，不存在则创建
        user_email = user_info['userPrincipalName']
        user = User.query.filter_by(email=user_email).first()
        
        if not user:
            # 创建新用户
            display_name = user_info.get('displayName', '').split()
            first_name = display_name[0] if display_name else ''
            last_name = display_name[-1] if len(display_name) > 1 else ''
            
            user = User(
                email=user_email,
                username=user_info.get('displayName', user_email),
                first_name=first_name,
                last_name=last_name,
                is_entra_user=True
            )
            db.session.add(user)
            db.session.commit()
            current_app.logger.info(f"Created new Entra ID user: {user_email}")
        
        # 登录用户
        login_user(user)
        
        # 将token保存到session中，以便后续使用
        session['access_token'] = result.get('access_token')
        session['refresh_token'] = result.get('refresh_token')
        session['id_token'] = result.get('id_token')
        
        # 重定向到主页或next参数指定的URL
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.dashboard')
        
        flash(f'您好，{user.username}！您已通过Microsoft账号成功登录。', 'success')
        return redirect(next_page)
    
    except Exception as e:
        current_app.logger.error(f"Entra ID登录出错: {str(e)}")
        flash('Microsoft登录过程中发生错误', 'danger')
        return redirect(url_for('auth.login'))

# 注册功能可选，暂不实现 