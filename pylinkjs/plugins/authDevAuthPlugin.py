# --------------------------------------------------
#    Imports
# --------------------------------------------------
import os
import tornado


# --------------------------------------------------
#    Plugin
# --------------------------------------------------
class pluginDevAuth:
    def __init__(self, login_page_url='authDevAuthPlugin_Login.html', logout_post_action_url='/'):
        self._kwargs = {
            'login_handler': DevAuthLoginHandler,
            'logout_handler': DevAuthLogoutHandler,
            'login_page_url': login_page_url,
            'logout_post_action_url': logout_post_action_url}

    def register(self, kwargs):
        # merge the dictionaries
        kwargs.update(self._kwargs)


# --------------------------------------------------
#    LoginHandler
# --------------------------------------------------
class DevAuthLoginHandler(tornado.web.RequestHandler):
    async def get(self):
        f = open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'authDevAuthPlugin_Login.html'))
        self.write(f.read())

    async def post(self):
        self.set_secure_cookie("user_auth_username", self.request.arguments['username'][0])
        self.set_secure_cookie("user_auth_method", 'DevAuth')
        self.redirect('/')


# --------------------------------------------------
#    LogoutHandler
# --------------------------------------------------
class DevAuthLogoutHandler(tornado.web.RequestHandler):
    async def get(self):
        # read the user and the access token
        self.clear_cookie('user_auth_username')
        self.clear_cookie('user_auth_method')

        self.redirect(self.application.settings['logout_post_action_url'])
