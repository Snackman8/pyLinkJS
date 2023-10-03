# --------------------------------------------------
#    Imports
# --------------------------------------------------
import logging
from urllib.parse import urlparse, parse_qs
from pylinkjs.PyLinkJS import run_pylinkjs_app, execute_in_subprocess


# --------------------------------------------------
#    Constants
# --------------------------------------------------
PORT = 9150


# --------------------------------------------------
#    Handlers
# --------------------------------------------------
def ready(jsc, *args):
    """ called when a webpage creates a new connection the first time on load """
    if args[1] == '/html_output':
        jsc['#mydiv'].html = 'Hello World!'


def handle_404(path, uri, *args):
    # handle URLS that do not have html pages
    if path == 'text_output':
        content_type = 'text/plain'
        status_code = 200
        html = 'THIS IS PLAIN TEXT'
        return (html, content_type, status_code)
    elif path == 'html_output':
        content_type = 'text/html'
        status_code = 200
        html = '<div style="color:red">THIS IS HTML TEXT</div><div id=mydiv></div>'
        return (html, content_type, status_code)


# --------------------------------------------------
#    Main
# --------------------------------------------------
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(relativeCreated)6d %(threadName)s %(message)s')
    run_pylinkjs_app(default_html='test_404_app.html', on_404=handle_404, port=PORT)
