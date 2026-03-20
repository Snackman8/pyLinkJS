# --------------------------------------------------
#    Imports
# --------------------------------------------------
import argparse
import logging
import os
from pylinkjs.PyLinkJS import run_pylinkjs_app
from pylinkjs.plugins.authLDAPAuthPlugin import pluginLDAPAuth


# --------------------------------------------------
#    Event Handlers
# --------------------------------------------------
def ready(jsc, *args):
    """ called when a webpage creates a new connection the first time on load """
    if args[1] == '/':
        jsc['#user_name'].html = jsc.user_auth_username if jsc.user_auth_username is not None else 'Guest'


# --------------------------------------------------
#    Main
# --------------------------------------------------
if __name__ == '__main__':
    # setup the logger
    logging.basicConfig(level=logging.DEBUG, format='%(relativeCreated)6d %(threadName)s %(message)s')

    # handle the --port argument
    parser = argparse.ArgumentParser(description='PyLinkJS LDAP Auth Example')
    parser.add_argument('--port', type=int, required=False, default=8300)
    parser.add_argument('--cookie_secret', help='cookie signing secret for the example app', required=False, default='CHANGEME')
    parser.add_argument('--ldap_server', help='LDAP Server, i.e. ldap://localhost', required=True)
    parser.add_argument('--ldap_base', help='LDAP Base, i.e. dc=example,dc=com', required=True)
    parser.add_argument('--ldap_group', help='LDAP Group to authenticate against, i.e. developers', required=True)
    args = vars(parser.parse_args())

    # init the ldap auth plugin
    ldap_plugin = pluginLDAPAuth(ldap_server=args['ldap_server'],
                                 ldap_base=args['ldap_base'],
                                 ldap_group=args['ldap_group'])

    # run the app
    run_pylinkjs_app(default_html='ldap_auth.html',
                     html_dir=os.path.dirname(__file__),
                     internal_polling_interval=0.025,
                     port=args['port'],
                     plugins=[ldap_plugin],
                     cookie_secret=args['cookie_secret'])
