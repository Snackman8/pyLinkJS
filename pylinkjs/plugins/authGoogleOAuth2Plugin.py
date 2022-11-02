# --------------------------------------------------
#    Imports
# --------------------------------------------------
import requests
import tornado.auth
import urllib


# --------------------------------------------------
#    Plugin
# --------------------------------------------------
class pluginGoogleOAuth2:
    def __init__(self, client_id, secret, redirect_url, logout_post_action_url='/'):
        self._kwargs = {
            'login_handler': GoogleOAuth2LoginHandler,
            'logout_handler': GoogleOAuth2LogoutHandler,
            'logout_post_action_url': logout_post_action_url,
            'google_oauth': {"key": client_id, "secret": secret},
            'google_oauth_redirect_uri': redirect_url}

    @property
    def auth_method(self):
        return 'GoogleOAuth2'
    
    def register(self, kwargs):
        # merge the dictionaries
        kwargs.update(self._kwargs)


# --------------------------------------------------
#    LoginHandler
# --------------------------------------------------
class GoogleOAuth2LoginHandler(tornado.web.RequestHandler,
                               tornado.auth.GoogleOAuth2Mixin):
    async def get(self):
        if self.get_argument('code', False):
            access = await self.get_authenticated_user(
                redirect_uri=self.settings['google_oauth_redirect_uri'],
                code=self.get_argument('code'))
            access_token = access["access_token"]
            user = await self.oauth2_request("https://www.googleapis.com/oauth2/v1/userinfo", access_token=access_token)
            self.set_secure_cookie("user_auth_access_token", access_token)
            self.set_secure_cookie('user_auth_method', 'GoogleOAuth2')
            self.set_secure_cookie("user_auth_name", user['name'])
            self.set_secure_cookie("user_auth_username", user['email'])
            self.redirect(urllib.parse.parse_qs(self.get_argument('state', '')).get('next', ['/'])[0])
        else:
            self.authorize_redirect(
                redirect_uri=self.settings['google_oauth_redirect_uri'],
                client_id=self.settings['google_oauth']['key'],
                scope=['profile', 'email'],
                response_type='code',
                extra_params={'approval_prompt': 'auto', 'state': f'next={self.get_argument("next", "/")}'})


# --------------------------------------------------
#    LogoutHandler
# --------------------------------------------------
class GoogleOAuth2LogoutHandler(tornado.web.RequestHandler):
    async def get(self):
        # read the user and the access token
        access_token = self.get_secure_cookie('user_auth_acess_token')
        if access_token is None:
            access_token = b''
        access_token = access_token.decode()

        url = f'https://oauth2.googleapis.com/revoke?token={access_token}'
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        requests.post(url, headers=headers)
        self.clear_cookie('user_auth_access_token')
        self.clear_cookie('user_auth_method')
        self.clear_cookie('user_auth_name')
        self.clear_cookie('user_auth_username')

        self.redirect(self.application.settings['logout_post_action_url'])
