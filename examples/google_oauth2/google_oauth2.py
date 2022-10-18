# --------------------------------------------------
#    Imports
# --------------------------------------------------
import argparse
import logging
from pylinkjs.PyLinkJS import run_pylinkjs_app
from pylinkjs.plugins.authGoogleOAuth2Plugin import pluginGoogleOAuth2


# --------------------------------------------------
#    Event Handlers
# --------------------------------------------------
def ready(jsc, *args):
    """ called when a webpage creates a new connection the first time on load """
    if args[1] == '/':
        jsc['#user_name'].html = jsc.user_name if jsc.user_name is not None else 'Guest'
        jsc['#user_email'].html = jsc.user_email if jsc.user_email is not None else 'N/A'


# --------------------------------------------------
#    Main
# --------------------------------------------------
if __name__ == '__main__':
    # parse the arguments
    parser = argparse.ArgumentParser(description='PyLinkJS Google Oauth2 Example')
    parser.add_argument('--oauth2_clientid', help='google oath2 client id', required=True)
    parser.add_argument('--oauth2_secret', help='google oath2 secret', required=True)
    args = vars(parser.parse_args())

    # configure logger
    logging.basicConfig(level=logging.DEBUG, format='%(relativeCreated)6d %(threadName)s %(message)s')

    # define the port
    port = 8300
    
    # init the google oauth2 plugin
    google_oauth2_plugin = pluginGoogleOAuth2(client_id=args['oauth2_clientid'],
                                              secret=args['oauth2_secret'],
                                              port=port,
                                              logout_post_action_url='/')

    # run the application
    run_pylinkjs_app(default_html='google_oauth2.html',
                     port=port,
                     plugins=[google_oauth2_plugin])
