# --------------------------------------------------
#    Imports
# --------------------------------------------------
from functools import partial
import inspect
import queue
import json
import os
import random
import sys
import threading
import traceback
import time
import tornado.web
import tornado.websocket
from tornado.ioloop import IOLoop
from tornado.platform.asyncio import  AnyThreadEventLoopPolicy
import asyncio

# --------------------------------------------------
#    Constants
# --------------------------------------------------
CONTEXTS = {}
RETVALS = {}
INCOMING_PKT_QUEUE = queue.Queue()


# --------------------------------------------------
#    Functions
# --------------------------------------------------
def get_context_event_time_ms(context_id):
    return CONTEXTS[context_id]['event_time_ms']


async def eval_js_code(context_id, js_code, no_wait=False):
    # send the javascript to the browser using the websocket
    ws = CONTEXTS[context_id]['websocket']
    pkt = {'id': 'py_' + str(random.random()),
           'cmd': 'eval_js',
           'js_code': js_code,
           'no_wait': no_wait}
    if CONTEXTS[context_id]['thread_id'] != threading.get_ident():
        IOLoop.instance().add_callback(ws.write_message, json.dumps(pkt))
    else:
        ws.write_message(json.dumps(pkt))
    
    if no_wait:
        return 0

    while pkt['id'] not in RETVALS:
        await asyncio.sleep(0)

    retval = RETVALS[pkt['id']]
    del RETVALS[pkt['id']]
    return retval
        

async def js_return_value(_cid, caller_id, retval):
    RETVALS[caller_id] = retval
    

# --------------------------------------------------
#    Thread Workers
# --------------------------------------------------
async def callback_dispatcher(caller_globals):
    while not INCOMING_PKT_QUEUE.empty():
        ctx, js_data = INCOMING_PKT_QUEUE.get()

        if js_data['cmd'] == 'call_py':
            try:
                func = None
                if js_data['py_func_name'] in caller_globals:
                    func = caller_globals[js_data['py_func_name']]
                if js_data['py_func_name'] in locals():
                    func = locals()[js_data['py_func_name']]
                elif js_data['py_func_name'] in globals():
                    func = globals()[js_data['py_func_name']]
                if func:
                    await func(ctx, *js_data['args'])
                else:
                    raise Exception('No function found with name "%s"' % js_data['py_func_name'])
            except:
                sys.stderr.write(traceback.format_exc())


# --------------------------------------------------
#    Tornado Request Handlers
# --------------------------------------------------
class PyLinkJSWebSocketHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        # create a context
        self.set_nodelay(True)
        context_id = self.request.path
        CONTEXTS[context_id] = {'websocket': self, 'thread_id': threading.get_ident()}
        if 'on_context_open' in self.application.settings:
            self.application.settings['on_context_open'](context_id)

    def on_message(self, message):
        context_id = self.request.path
        js_data = json.loads(message)

        # correct the time between different client and server
        if js_data['cmd'] == 'synchronize_time':
            CONTEXTS[context_id]['time_offset_ms'] = js_data['event_time_ms'] - time.time() * 1000
        CONTEXTS[context_id]['event_time_ms'] = js_data['event_time_ms'] - CONTEXTS[context_id]['time_offset_ms']            
        del js_data['event_time_ms']

        # put the packet in the queue
        INCOMING_PKT_QUEUE.put((context_id, js_data), True, None)        

    def on_close(self):
        # clean up the context
        context_id = self.request.path
        if 'on_context_close' in self.application.settings:
            self.application.settings['on_context_close'](context_id)
        del CONTEXTS[context_id]
        
        
class MainHandler(tornado.web.RequestHandler):
    def get(self):
        # strip off the leading slash, then combine with web directory
        filename = os.path.abspath(os.path.join(self.application.settings['html_dir'], self.request.path[1:]))

        print(filename)

        # default to index.html if this is a directory
        if os.path.isdir(filename):
            filename = os.path.join(filename, self.application.settings['default_html'])

        # return 404 if file does not exist or is a directory
        if not os.path.exists(filename):
            raise tornado.web.HTTPError(404)

        # load the file
        f = open(filename, 'rb')
        b = f.read()
        f.close()

        # monkey patch in the websocket hooks
        if filename.endswith('.html'):
            monkeypatch_filename = os.path.join(os.path.dirname(__file__), 'monkey_patch.js')
            f = open(monkeypatch_filename, 'rb')
            mps = f.read()
            f.close()
            b = b + b'\n' + mps
        
        # serve the page
        self.write(b)
        

# --------------------------------------------------
#    Main
# --------------------------------------------------
def run_pylinkjs_app(**kwargs):
    if 'port' not in kwargs:
        kwargs['port'] = 8300
    if 'default_html' not in kwargs:
        kwargs['default_html'] = 'index.html'
    if 'html_dir' not in kwargs:
        kwargs['html_dir'] = '.'
        
    asyncio.set_event_loop_policy(AnyThreadEventLoopPolicy())
    app = tornado.web.Application([
        (r"/websocket/.*", PyLinkJSWebSocketHandler),
        (r"/.*", MainHandler),],
        default_html = kwargs['default_html'],
        html_dir = kwargs['html_dir']
    )

    caller_globals = inspect.stack()[1][0].f_globals
    
    # start the tornado server
    app.listen(kwargs['port'])
    app.settings['on_context_close'] = kwargs.get('onContextClose', None)
    app.settings['on_context_open'] = kwargs.get('onContextOpen', None)
    tornado.ioloop.PeriodicCallback(partial(callback_dispatcher, caller_globals), 1).start()
    IOLoop.current().start()


# if __name__ =='__main__':
#     # parse the args
#     parser = argparse.ArgumentParser(description='Serve a pylinkjs application')
# #    parser.add_argument('--nobrowser', type=int, help='do not auto launch the browser', default=False)    
#     parser.add_argument('--port', type=int, help='port to run server on', default=8300)
#     args = parser.parse_args()
#     run(vars(args))

