# --------------------------------------------------
#    Imports
# --------------------------------------------------
import argparse
import logging
import os
from pylinkjs.PyLinkJS import run_pylinkjs_app
from pylinkjs.plugins.authGoogleOAuth2Plugin import pluginGoogleOAuth2


# --------------------------------------------------
#    Event Handlers
# --------------------------------------------------
def ready(jsc, *args):
    """ called when a webpage creates a new connection the first time on load """
    if args[1] == '/':
        jsc['#user_name'].html = jsc.user_auth_username if jsc.user_auth_username is not None else 'Guest'
        jsc['#user_email'].html = jsc.user_auth_email if jsc.user_auth_email is not None else 'N/A'


# --------------------------------------------------
#    Main
# --------------------------------------------------
if __name__ == '__main__':
    # setup the logger
    logging.basicConfig(level=logging.DEBUG, format='%(relativeCreated)6d %(threadName)s %(message)s')
    
    # handle the --port argument
    parser = argparse.ArgumentParser(description='PyLinkJS Google Oauth2 Example')
    parser.add_argument('--port', type=int, required=False, default=8300)
    parser.add_argument('--oauth2_clientid', help='google oath2 client id', required=True)
    parser.add_argument('--oauth2_secret', help='google oath2 secret', required=True)
    parser.add_argument('--oauth2_redirect_url', help='google oath2 redirect url', default='http://localhost:8300')    
    args = vars(parser.parse_args())
    
    # init the google oauth2 plugin
    google_oauth2_plugin = pluginGoogleOAuth2(client_id=args['oauth2_clientid'],
                                              secret=args['oauth2_secret'],
                                              redirect_url=f'{args["oauth2_redirect_url"]}/login')

    # run the app
    run_pylinkjs_app(default_html='google_oauth2.html', html_dir=os.path.dirname(__file__), internal_polling_interval=0.025, port=args['port'], plugins=[google_oauth2_plugin])
