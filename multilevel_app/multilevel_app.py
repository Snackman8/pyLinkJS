import logging
from pylinkjs.PyLinkJS import run_pylinkjs_app


def button_clicked(jsc):
    """ simple example of a button click """
    print('ROOT LEVEL')


def ready(jsc, *args):
    """ called when a webpage creates a new connection the first time on load """
    print('ROOT CONNECT')


def reconnect(jsc, *args):
    print('ROOT RECONNECT')


if __name__ == '__main__':
    # start the thread and the app
    logging.basicConfig(level=logging.DEBUG, format='%(relativeCreated)6d %(threadName)s %(message)s')
    run_pylinkjs_app(default_html='multilevel_app.html')
