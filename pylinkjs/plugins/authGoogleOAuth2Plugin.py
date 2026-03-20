# --------------------------------------------------
#    Imports
# --------------------------------------------------
import secrets
import requests
import tornado.auth
import tornado.web
from pylinkjs.PyLinkJS import LoginHandler, LogoutHandler


# --------------------------------------------------
#    Plugin
# --------------------------------------------------
class pluginGoogleOAuth2:
    requires_cookie_secret = True

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
class GoogleOAuth2LoginHandler(LoginHandler,
                               tornado.auth.GoogleOAuth2Mixin):
    _state_cookie_name = 'pylinkjs_google_oauth_state'
    _next_cookie_name = 'pylinkjs_google_oauth_next'

    async def get(self):
        if self.get_argument('code', False):
            expected_state = self.get_secure_cookie(self._state_cookie_name)
            next_url = self.get_secure_cookie(self._next_cookie_name)
            actual_state = self.get_argument('state', '')
            if expected_state is None or not secrets.compare_digest(expected_state.decode(), actual_state):
                self.clear_cookie(self._state_cookie_name)
                self.clear_cookie(self._next_cookie_name)
                raise tornado.web.HTTPError(403)

            self.clear_cookie(self._state_cookie_name)
            self.clear_cookie(self._next_cookie_name)
            access = await self.get_authenticated_user(
                redirect_uri=self.settings['google_oauth_redirect_uri'],
                code=self.get_argument('code'))
            access_token = access["access_token"]
            user = await self.oauth2_request("https://www.googleapis.com/oauth2/v1/userinfo", access_token=access_token)

            cookies = {
                self.settings['cookiename_user_auth_access_token']: access_token,
                self.settings['cookiename_user_auth_username']: user['name'],
                self.settings['cookiename_user_auth_email']: user['email'],
                self.settings['cookiename_user_auth_method']: 'GoogleOAuth2'}
    
            # delegeate to the login hanlder get_handler which will set the cookies and display the login_html_page
            for k, v in cookies.items():
                self.set_secure_cookie(k, v)
            self.redirect(next_url.decode() if next_url is not None else '/')
        else:
            next_url = self.get_argument('next', '/')
            state = secrets.token_urlsafe(32)
            self.set_secure_cookie(self._state_cookie_name, state, httponly=True)
            self.set_secure_cookie(self._next_cookie_name, next_url, httponly=True)
            self.authorize_redirect(
                redirect_uri=self.settings['google_oauth_redirect_uri'],
                client_id=self.settings['google_oauth']['key'],
                scope=['profile', 'email'],
                response_type='code',
                extra_params={'approval_prompt': 'auto', 'state': state})


# --------------------------------------------------
#    LogoutHandler
# --------------------------------------------------
class GoogleOAuth2LogoutHandler(LogoutHandler):
    async def get(self):
        # read the user and the access token
        access_token = self.get_secure_cookie(self.settings['cookiename_user_auth_access_token'])
        if access_token is None:
            access_token = b''
        access_token = access_token.decode()

        url = f'https://oauth2.googleapis.com/revoke?token={access_token}'
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        requests.post(url, headers=headers)

        # build the list of cookies to clear when logging out
        cookie_list = [self.settings['cookiename_user_auth_access_token'],
                       self.settings['cookiename_user_auth_username'],
                       self.settings['cookiename_user_auth_email'],
                       self.settings['cookiename_user_auth_method'],]

        # delegate to the logout get_handler which will clear the cookies then redirect to the logout_post_action_url
        self.get_handler(cookie_list)
