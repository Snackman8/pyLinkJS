# --------------------------------------------------
#    Imports
# --------------------------------------------------
import argparse
import logging
import os
from pylinkjs.PyLinkJS import run_pylinkjs_app


# --------------------------------------------------
#    Event Handlers
# --------------------------------------------------
def ready(jsc, *args):
    """ called when a webpage creates a new connection the first time on load """
    print('Ready!')


# --------------------------------------------------
#    Main
# --------------------------------------------------
if __name__ == '__main__':
    # setup the logger
    logging.basicConfig(level=logging.DEBUG, format='%(relativeCreated)6d %(threadName)s %(message)s')
    
    # handle the --port argument
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, required=False, default=8300)
    args = vars(parser.parse_args())

    # run the app
    run_pylinkjs_app(default_html='bootstrap_cheatsheet.html', html_dir=os.path.dirname(__file__), internal_polling_interval=0.025, port=args['port'])
