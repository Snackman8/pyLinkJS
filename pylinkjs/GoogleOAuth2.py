import requests
import urllib
import tornado.auth


class GoogleOAuth2LoginHandler(tornado.web.RequestHandler,
                               tornado.auth.GoogleOAuth2Mixin):
    async def get(self):
        if self.get_argument('code', False):
            print(self.settings['google_oauth_redirect_uri'])
            access = await self.get_authenticated_user(
                redirect_uri=self.settings['google_oauth_redirect_uri'],
                code=self.get_argument('code'))
            access_token = access["access_token"]
            user = await self.oauth2_request("https://www.googleapis.com/oauth2/v1/userinfo", access_token=access_token)
            self.set_secure_cookie("user", user['name'])
            self.set_secure_cookie("access_token", access_token)
            print('writing secure token')
            self.redirect(urllib.parse.parse_qs(self.get_argument('state', '')).get('next', ['/'])[0])
        else:
            self.authorize_redirect(
                redirect_uri=self.settings['google_oauth_redirect_uri'],
                client_id=self.settings['google_oauth']['key'],
                scope=['profile', 'email'],
                response_type='code',
                extra_params={'approval_prompt': 'auto', 'state': f'next={self.get_argument("next", "/")}'})


class LogoutHandler(tornado.web.RequestHandler):
    async def get(self):
        # read the user and the access token
        access_token = self.get_secure_cookie('access_token')
        if access_token is None:
            access_token = b''
        access_token = access_token.decode()

        user = self.get_secure_cookie('user')
        if user is None:
            user = b''
        user = user.decode()

        url = f'https://oauth2.googleapis.com/revoke?token={access_token}'
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        requests.post(url, headers=headers)
        self.write(f'{user} has been logged out')
        self.clear_cookie('user')
        self.clear_cookie('access_token')
