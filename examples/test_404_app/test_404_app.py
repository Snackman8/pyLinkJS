# --------------------------------------------------
#    Imports
# --------------------------------------------------
import argparse
import logging
import os
from pylinkjs.PyLinkJS import run_pylinkjs_app


# --------------------------------------------------
#    Handlers
# --------------------------------------------------
def ready(jsc, *args):
    """ called when a webpage creates a new connection the first time on load """
    if args[1] == '/html_output':
        jsc['#mydiv'].html = 'Hello World!'


def handle_404(path, uri, host, extra_settings, headers, body, method, *args):
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
    # setup the logger
    logging.basicConfig(level=logging.DEBUG, format='%(relativeCreated)6d %(threadName)s %(message)s')
    
    # handle the --port argument
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, required=False, default=8300)
    args = vars(parser.parse_args())

    # run the app
    run_pylinkjs_app(default_html='test_404_app.html', html_dir=os.path.dirname(__file__), internal_polling_interval=0.025, on_404=handle_404, port=args['port'])
