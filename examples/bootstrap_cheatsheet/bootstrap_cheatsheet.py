# --------------------------------------------------
#    Imports
# --------------------------------------------------
import logging
from pylinkjs.PyLinkJS import run_pylinkjs_app
from pylinkjs.plugins.uiFormBuilder import pluginFormBuilder


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
    # configure logger
    logging.basicConfig(level=logging.DEBUG, format='%(relativeCreated)6d %(threadName)s %(message)s')

    # define the port
    port = 8301

    # init the formBuilder plugin
    formBuilder = pluginFormBuilder()

    # run the application
    run_pylinkjs_app(default_html='bootstrap_cheatsheet.html',
                     port=port,
                     plugins=[formBuilder])
