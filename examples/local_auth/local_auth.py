# --------------------------------------------------
#    Imports
# --------------------------------------------------
import argparse
import logging
import os
from pylinkjs.PyLinkJS import run_pylinkjs_app
from pylinkjs.plugins.authLocalAuthAdminPlugin import pluginLocalAuthAdmin
from pylinkjs.plugins.authLocalAuthPlugin import pluginLocalAuth


# --------------------------------------------------
#    Event Handlers
# --------------------------------------------------
def ready(jsc, *args):
    """ called when a webpage creates a new connection the first time on load """
    if args[1] == '/':
        jsc['#user_name'].html = jsc.user_auth_username if jsc.user_auth_username is not None else 'Guest'
        jsc['#auth_method'].html = jsc.user_auth_method if jsc.user_auth_method is not None else 'Unknown'


# --------------------------------------------------
#    Main
# --------------------------------------------------
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(relativeCreated)6d %(threadName)s %(message)s')

    parser = argparse.ArgumentParser(description='PyLinkJS Local Auth Example')
    parser.add_argument('--port', type=int, required=False, default=8302)
    parser.add_argument('--cookie_secret', help='cookie signing secret for the example app', required=False, default='CHANGEME')
    parser.add_argument('--db_path', help='path to the SQLite user database', required=False,
                        default=os.path.join(os.path.dirname(__file__), 'local_auth.sqlite3'))
    args = vars(parser.parse_args())

    local_auth_plugin = pluginLocalAuth(db_path=args['db_path'])
    local_auth_admin_plugin = pluginLocalAuthAdmin(db_path=args['db_path'])

    run_pylinkjs_app(default_html='local_auth.html',
                     html_dir=os.path.dirname(__file__),
                     internal_polling_interval=0.025,
                     port=args['port'],
                     plugins=[local_auth_plugin, local_auth_admin_plugin],
                     cookie_secret=args['cookie_secret'],
                     require_auth=True)
