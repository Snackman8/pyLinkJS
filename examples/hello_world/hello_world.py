import argparse
import logging
import os
import threading
import time
from pylinkjs.PyLinkJS import run_pylinkjs_app, Code, get_broadcast_jsclients


def ready(jsc, *args):
    """ called when a webpage creates a new connection the first time on load """
    print('Ready', args)


def reconnect(jsc, *args):
    """ called when a webpage automatically reconnects a broken connection """
    print('Reconnect', args)


def button_clicked(jsc, a, b, c):
    """ simple example of a button click """
    retval = jsc.eval_js_code(77)
    print('GOT BACK', retval)
    print('TEST', jsc['#divout'].html)
    jsc['#divout'].html = 'AS"\'DF2' + str(time.time())
    jsc['#divout'].css.color = 'red'
    jsc['#divout'].click = Code('function() { console.log("AA"); }')


def button_broadcast(jsc):
    """ example of how to broadcast a change to all webpages """
    t = time.time()
    for bjsc in jsc.get_broadcast_jscs():
        bjsc['#divout_broadcast'].html = t


def py_select_changed(jsc, a, b, c):
    print(a, b, c)


def start_threaded_automatic_update():
    """ example of how to run a periodic update from a different thread """
    def thread_worker():
        # loop forever
        while True:
            t = time.time()
            for jsc in get_broadcast_jsclients('/'):
                jsc['#divout_automatic_broadcast'].html = t
            time.sleep(1)

    # start the thread
    t = threading.Thread(target=thread_worker, daemon=True)
    t.start()


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
    
    # start the background thread for this app
    start_threaded_automatic_update()

    # run the app
    run_pylinkjs_app(default_html='hello_world.html', html_dir=os.path.dirname(__file__), internal_polling_interval=0.025, port=args['port'])
