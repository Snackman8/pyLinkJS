# --------------------------------------------------
#    Imports
# --------------------------------------------------
import argparse
import logging
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
    # parse the arguments
    parser = argparse.ArgumentParser(description='PyLinkJS Development Auth Example')
    args = vars(parser.parse_args())

    # configure logger
    logging.basicConfig(level=logging.DEBUG, format='%(relativeCreated)6d %(threadName)s %(message)s')

    # define the port
    port = 8330
    
    # init the ldap auth plugin
    devauth_plugin = pluginDevAuth()

    # run the application
    run_pylinkjs_app(default_html='dev_auth.html',
                     port=port,
                     plugins=[devauth_plugin])
