# --------------------------------------------------
#    Imports
# --------------------------------------------------
import os
from pylinkjs.PyLinkJS import LoginHandler, LogoutHandler


# --------------------------------------------------
#    Plugin
# --------------------------------------------------
class pluginDevAuth:
    def __init__(self, login_html_page=None, logout_post_action_url=None):
        # use a default login_html_page if none is provided
        if login_html_page is None:
            login_html_page = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'authDevAuthPlugin_Login.html')

        # build the arguments used by LoginHandler and LogoutHandler
        self._kwargs = {
            'login_handler': DevAuthLoginHandler,
            'logout_handler': DevAuthLogoutHandler,
            'login_html_page': login_html_page, }

        # set the logout post action url if needed
        if logout_post_action_url is not None:
            self._kwargs['logout_post_action_url'] = logout_post_action_url

    def register(self, kwargs):
        # merge the dictionaries
        kwargs.update(self._kwargs)


# --------------------------------------------------
#    LoginHandler
# --------------------------------------------------
class DevAuthLoginHandler(LoginHandler):
    async def post(self):
        # build the cookie dictionary to set
        cookies = {
            self.settings['cookiename_user_auth_username']: self.request.arguments['username'][0],
            self.settings['cookiename_user_auth_method']: 'DevAuth'}
    
        # delegeate to the login hanlder get_handler which will set the cookies and display the login_html_page
        self.post_handler(cookies)


# --------------------------------------------------
#    LogoutHandler
# --------------------------------------------------
class DevAuthLogoutHandler(LogoutHandler):
    async def get(self):
        # build the lsit of cookies to clear when logging out
        cookie_list = [self.settings['cookiename_user_auth_username'],
                       self.settings['cookiename_user_auth_method'] ]

        # delegate to the logout get_handler which will clear the cookies then redirect to the logout_post_action_url
        self.get_handler(cookie_list)
