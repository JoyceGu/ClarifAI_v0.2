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
    
    # Microsoft Entra ID login link
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
            flash('Invalid email or password', 'danger')
            
    # Get test accounts
    test_accounts = [
        {'role': 'PM', 'email': 'pm@test.com', 'password': 'password123'},
        {'role': 'Researcher', 'email': 'researcher@test.com', 'password': 'password123'}
    ]
    
    return render_template('auth/login.html', form=form, test_accounts=test_accounts, ms_login_url=ms_login_url)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been successfully logged out', 'info')
    return redirect(url_for('auth.login'))

@auth.route('/entra-login')
def entra_login():
    """Microsoft Entra ID login entry point"""
    entra_id_provider = get_entra_id_provider()
    if not entra_id_provider:
        flash('Microsoft Entra ID login not configured', 'warning')
        return redirect(url_for('auth.login'))
        
    # Generate authorization URL and redirect
    auth_url = entra_id_provider.get_login_url()
    return redirect(auth_url)

@auth.route('/callback')
def callback():
    """Handle Microsoft Entra ID callback"""
    entra_id_provider = get_entra_id_provider()
    if not entra_id_provider:
        flash('Microsoft Entra ID login not configured', 'warning')
        return redirect(url_for('auth.login'))
    
    try:
        # Verify state to prevent CSRF attacks
        if not entra_id_provider.verify_callback():
            flash('Invalid authentication request', 'danger')
            return redirect(url_for('auth.login'))
        
        # Get authorization code
        auth_code = request.args.get('code')
        if not auth_code:
            flash('Authentication failed', 'danger')
            return redirect(url_for('auth.login'))
        
        # Get token
        result = entra_id_provider.get_token_from_code(auth_code)
        if not result or 'access_token' not in result:
            flash('Failed to get access token', 'danger')
            return redirect(url_for('auth.login'))
        
        # Get user info
        user_info = entra_id_provider.get_user_info(result['access_token'])
        if not user_info or 'userPrincipalName' not in user_info:
            flash('Failed to get user information', 'danger')
            return redirect(url_for('auth.login'))
        
        # Check if user exists, create if not
        user_email = user_info['userPrincipalName']
        user = User.query.filter_by(email=user_email).first()
        
        if not user:
            # Create new user
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
        
        # Login user
        login_user(user)
        
        # Save token to session for later use
        session['access_token'] = result.get('access_token')
        session['refresh_token'] = result.get('refresh_token')
        session['id_token'] = result.get('id_token')
        
        # Redirect to home or URL specified by next parameter
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.dashboard')
        
        flash(f'Hello, {user.username}! You have successfully logged in with your Microsoft account.', 'success')
        return redirect(next_page)
    
    except Exception as e:
        current_app.logger.error(f"Entra ID login error: {str(e)}")
        flash('Error occurred during Microsoft login process', 'danger')
        return redirect(url_for('auth.login'))

# Registration feature optional, not implemented yet 