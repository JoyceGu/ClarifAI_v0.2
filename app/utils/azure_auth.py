"""
Microsoft Entra ID认证工具类
"""
import os
import msal
from flask import url_for, current_app, session, request
import requests
import uuid

class EntraIDAuthProvider:
    def __init__(self, app=None):
        self.client_id = None
        self.client_secret = None
        self.tenant_id = None
        self.authority = None
        self.scope = None
        self.redirect_path = None
        self.session_type = None
        
        if app is not None:
            self.init_app(app)
            
    def init_app(self, app):
        # 从环境变量或配置中获取配置信息
        self.client_id = app.config.get('ENTRA_CLIENT_ID', os.environ.get('ENTRA_CLIENT_ID'))
        self.client_secret = app.config.get('ENTRA_CLIENT_SECRET', os.environ.get('ENTRA_CLIENT_SECRET'))
        self.tenant_id = app.config.get('ENTRA_TENANT_ID', os.environ.get('ENTRA_TENANT_ID'))
        self.authority = app.config.get('ENTRA_AUTHORITY', 
                                       os.environ.get('ENTRA_AUTHORITY', 
                                                     f"https://login.microsoftonline.com/{self.tenant_id}"))
        self.scope = app.config.get('ENTRA_SCOPE', os.environ.get('ENTRA_SCOPE', 'user.read')).split()
        self.redirect_path = app.config.get('ENTRA_REDIRECT_PATH', os.environ.get('ENTRA_REDIRECT_PATH', '/auth/callback'))
        self.session_type = app.config.get('SESSION_TYPE', 'filesystem')
        
        # 注册回调路由
        # 在外部定义路由，这里只提供工具类
    
    def _build_msal_app(self):
        """构建MSAL应用配置"""
        return msal.ConfidentialClientApplication(
            self.client_id, 
            authority=self.authority,
            client_credential=self.client_secret
        )
    
    def _build_auth_url(self, callback_url=None, state=None):
        """构建授权URL"""
        if callback_url is None:
            callback_url = url_for('auth.callback', _external=True)
            
        # 生成唯一的状态值用于防止CSRF攻击
        state = state or str(uuid.uuid4())
        session["state"] = state
        
        return self._build_msal_app().get_authorization_request_url(
            self.scope,
            state=state,
            redirect_uri=callback_url
        )
    
    def get_login_url(self, callback_url=None):
        """获取登录URL"""
        return self._build_auth_url(callback_url)
    
    def get_token_from_code(self, auth_code, callback_url=None):
        """使用授权码获取访问令牌"""
        if callback_url is None:
            callback_url = url_for('auth.callback', _external=True)
            
        result = self._build_msal_app().acquire_token_by_authorization_code(
            auth_code,
            scopes=self.scope,
            redirect_uri=callback_url
        )
        
        if "error" in result:
            current_app.logger.error(f"Error acquiring token: {result.get('error_description', 'Unknown error')}")
            return None
            
        return result
    
    def get_user_info(self, access_token):
        """使用访问令牌获取用户信息"""
        if not access_token:
            return None
            
        graph_data = requests.get(
            "https://graph.microsoft.com/v1.0/me",
            headers={'Authorization': f'Bearer {access_token}'},
        ).json()
        
        return graph_data
    
    def verify_callback(self, state=None):
        """验证回调，防止CSRF攻击"""
        if state is None:
            state = request.args.get('state', '')
            
        session_state = session.get("state", '')
        
        return session_state == state 