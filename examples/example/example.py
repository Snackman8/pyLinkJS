""" Example Web App """
# --------------------------------------------------
#    Imports
# --------------------------------------------------
import argparse
import datetime
import os
import logging
from pylinkjs.PyLinkJS import run_pylinkjs_app, Code


# --------------------------------------------------
#    Event Handlers
# --------------------------------------------------
def button_clicked(jsc, a, b):
    """ simple example of a button click """
    jsc['#divout'].html = "Current Time: " + datetime.datetime.now().strftime('%H:%M:%S')
    jsc['#divout'].css.color = 'red'
    jsc['#divout'].click = Code('function() { alert("AA"); }')


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
    run_pylinkjs_app(default_html='example.html', html_dir=os.path.dirname(__file__), internal_polling_interval=0.025, port=args['port'])
