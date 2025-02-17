# --------------------------------------------------
#    Imports
# --------------------------------------------------
import argparse
import logging
import os
from pylinkjs.PyLinkJS import run_pylinkjs_app
from pylinkjs.plugins.authDevAuthPlugin import pluginDevAuth


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
    parser = argparse.ArgumentParser(description='PyLinkJS Development Auth Example')    
    parser.add_argument('--port', type=int, required=False, default=8300)
    args = vars(parser.parse_args())

    # init the ldap auth plugin
    devauth_plugin = pluginDevAuth()

    # run the app
    run_pylinkjs_app(default_html='dev_auth.html', html_dir=os.path.dirname(__file__), internal_polling_interval=0.025, port=args['port'], plugins=[devauth_plugin])
