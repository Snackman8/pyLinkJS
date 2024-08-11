""" Example Web App """
# --------------------------------------------------
#    Imports
# --------------------------------------------------
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
#   Main
# --------------------------------------------------
def main(args):
    # start the thread and the app
    args['port'] = args.get('port', 8300)
    logging.basicConfig(level=logging.DEBUG, format='%(relativeCreated)6d %(threadName)s %(message)s')
    run_pylinkjs_app(default_html='example.html', html_dir=os.path.dirname(__file__), internal_polling_interval=0.025, port=args['port'])


if __name__ == '__main__':
    args = {}
    main(args)
