# --------------------------------------------------
#    Imports
# --------------------------------------------------
import os
import ldap
from pylinkjs.PyLinkJS import LoginHandler, LogoutHandler


# --------------------------------------------------
#    Plugin
# --------------------------------------------------
class pluginLDAPAuth:    
    def __init__(self, ldap_server, ldap_base, ldap_group, login_html_page=None, logout_post_action_url=None):
        # use a default login_html_page if none is provided
        if login_html_page is None:
            login_html_page = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'authLDAPAuthPlugin_Login.html')
        
        self._kwargs = {
            'login_handler': LDAPAuthLoginHandler,
            'logout_handler': LDAPAuthLogoutHandler,
            'login_html_page': login_html_page,
            'ldap_server': ldap_server,
            'ldap_base': ldap_base,
            'ldap_group': ldap_group}

        # set the logout post action url if needed
        if logout_post_action_url is not None:
            self._kwargs['logout_post_action_url'] = logout_post_action_url

    def register(self, kwargs):
        # merge the dictionaries
        kwargs.update(self._kwargs)


# --------------------------------------------------
#    LoginHandler
# --------------------------------------------------
class LDAPAuthLoginHandler(LoginHandler):
    @classmethod
    def _check_ldap_login(cls, ldap_server, ldap_base, username, password, memberof_group):
        # connect to LDAP
        l = ldap.initialize(ldap_server)
    
        # get the gid of the group
        try:
            results = l.search_s('ou=Group,' + ldap_base, ldap.SCOPE_SUBTREE, f'(cn={memberof_group})', [])
        except ldap.SERVER_DOWN:
            return False
        if len(results) == 0:
            return False
        group_gidNumber = results[0][1]['gidNumber'][0].decode('ASCII')
    
        # given the uid of the user, get the cn (Full Name)
        results = l.search_s('ou=People,' + ldap_base, ldap.SCOPE_SUBTREE, f'(uid={username})', [])
        if len(results) == 0:
            return False
        cn = results[0][1]['cn'][0].decode('ASCII')
        user_gidNumber = results[0][1]['gidNumber'][0].decode('ASCII')
    
        # authenticate the user with LDAP
        try:
            l.simple_bind_s(f'cn={cn},ou=People,' + ldap_base, password)
        except ldap.INVALID_CREDENTIALS:
            return False
    
        # verify the user is a member of the group by groupid
        if group_gidNumber == user_gidNumber:
            return True
    
        # verify the user is a member by member id
        results = l.search_s('ou=Group,' + ldap_base, ldap.SCOPE_SUBTREE, f'(&(memberUid={username})(gidNumber={group_gidNumber}))', [])
        if len(results) > 0:
            return True
    
        # no match
        return False

    async def post(self):

        username = self.request.arguments['username'][0].decode('ASCII')
        password = self.request.arguments['password'][0].decode('ASCII')

        ldap_server = self.settings['ldap_server']
        ldap_base = self.settings['ldap_base']
        ldap_group = self.settings['ldap_group']

        result = self._check_ldap_login(ldap_server, ldap_base, username, password, ldap_group)
        if not result:
            filename = self.application.settings['login_html_page']
            with open(filename, 'r') as f:
                s = f.read()
            s = s.replace('{next_url}', self.request.headers.get('Referer', '/'))
            s = s.replace('{error_message}', 'Login Failed!')
            self.write(s)
            return
        cookies = {
            self.settings['cookiename_user_auth_username']: self.request.arguments['username'][0],
            self.settings['cookiename_user_auth_method']: 'LDAPAuth'}

        # delegeate to the login hanlder get_handler which will set the cookies and display the login_html_page
        self.post_handler(cookies)


# --------------------------------------------------
#    LogoutHandler
# --------------------------------------------------
class LDAPAuthLogoutHandler(LogoutHandler):
    async def get(self):
        # build the list of cookies to clear when logging out
        cookie_list = [self.settings['cookiename_user_auth_username'],
                       self.settings['cookiename_user_auth_method'] ]

        # delegate to the logout get_handler which will clear the cookies then redirect to the logout_post_action_url
        self.get_handler(cookie_list)
