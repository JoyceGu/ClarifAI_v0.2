"""
Microsoft Entra ID Authentication Utility Class
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
        # Get configuration from environment variables or app config
        self.client_id = app.config.get('ENTRA_CLIENT_ID', os.environ.get('ENTRA_CLIENT_ID'))
        self.client_secret = app.config.get('ENTRA_CLIENT_SECRET', os.environ.get('ENTRA_CLIENT_SECRET'))
        self.tenant_id = app.config.get('ENTRA_TENANT_ID', os.environ.get('ENTRA_TENANT_ID'))
        self.authority = app.config.get('ENTRA_AUTHORITY', 
                                       os.environ.get('ENTRA_AUTHORITY', 
                                                     f"https://login.microsoftonline.com/{self.tenant_id}"))
        self.scope = app.config.get('ENTRA_SCOPE', os.environ.get('ENTRA_SCOPE', 'user.read')).split()
        self.redirect_path = app.config.get('ENTRA_REDIRECT_PATH', os.environ.get('ENTRA_REDIRECT_PATH', '/auth/callback'))
        self.session_type = app.config.get('SESSION_TYPE', 'filesystem')
        
        # Register callback route
        # Routes are defined externally, this is just a utility class
    
    def _build_msal_app(self):
        """Build MSAL application configuration"""
        return msal.ConfidentialClientApplication(
            self.client_id, 
            authority=self.authority,
            client_credential=self.client_secret
        )
    
    def _build_auth_url(self, callback_url=None, state=None):
        """Build authorization URL"""
        if callback_url is None:
            callback_url = url_for('auth.callback', _external=True)
            
        # Generate unique state value to prevent CSRF attacks
        state = state or str(uuid.uuid4())
        session["state"] = state
        
        return self._build_msal_app().get_authorization_request_url(
            self.scope,
            state=state,
            redirect_uri=callback_url
        )
    
    def get_login_url(self, callback_url=None):
        """Get login URL"""
        return self._build_auth_url(callback_url)
    
    def get_token_from_code(self, auth_code, callback_url=None):
        """Get access token using authorization code"""
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
        """Get user information using access token"""
        if not access_token:
            return None
            
        graph_data = requests.get(
            "https://graph.microsoft.com/v1.0/me",
            headers={'Authorization': f'Bearer {access_token}'},
        ).json()
        
        return graph_data
    
    def verify_callback(self, state=None):
        """Verify callback to prevent CSRF attacks"""
        if state is None:
            state = request.args.get('state', '')
            
        session_state = session.get("state", '')
        
        return session_state == state 