# --------------------------------------------------
#    Imports
# --------------------------------------------------
from functools import partial
import inspect
import queue
import json
import os
import random
import time
import argparse
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
#    Webpage Functions
# --------------------------------------------------
async def ready(cid):
    print('READY!')


async def test(cid, a, b, c):
    js_code = """document.getElementById("a"); a.innerHTML="%s"; 2+2;""" % (time.time())
    retval = await eval_js_code(cid, js_code)
    print('TEST ' + str(retval))


# --------------------------------------------------
#    Functions
# --------------------------------------------------
async def eval_js_code(context_id, js_code, no_wait=False):
    # send the javascript to the browser using the websocket
    ws = CONTEXTS[context_id]['websocket']
    pkt = {'id': 'py_' + str(random.random()),
           'cmd': 'eval_js',
           'js_code': js_code,
           'no_wait': no_wait}
    IOLoop.instance().add_callback(ws.write_message, json.dumps(pkt))
    
    if no_wait:
        return 0

#    await IOLoop.current().run_in_executor(None, wait_for_return_value, pkt[''])
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
        cid, message = INCOMING_PKT_QUEUE.get()
        js_data = json.loads(message)
          
        if js_data['cmd'] == 'call_py':
            js_data['py_func_name']
            js_data['args']
              
            if js_data['py_func_name'] in caller_globals:
                await caller_globals[js_data['py_func_name']](cid, *js_data['args'])
            if js_data['py_func_name'] in locals():
                await locals()[js_data['py_func_name']](cid, *js_data['args'])
            elif js_data['py_func_name'] in globals():
                await globals()[js_data['py_func_name']](cid, *js_data['args'])


# --------------------------------------------------
#    Tornado Request Handlers
# --------------------------------------------------
class PyLinkJSWebSocketHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        # create a context
        self.set_nodelay(True)
        context_id = self.request.path
        CONTEXTS[context_id] = {'websocket': self}

    def on_message(self, message):
        context_id = self.request.path
        INCOMING_PKT_QUEUE.put((context_id, message), True, None)        

    def on_close(self):
        # clean up the context
        context_id = self.request.path
        del CONTEXTS[context_id]
        
        
class MainHandler(tornado.web.RequestHandler):
    def get(self):
        # strip off the leading slash, then combine with web directory
        filename = os.path.abspath(os.path.join(self.application.settings['html_dir'], self.request.path[1:]))

        # default to index.html if this is a directory
        if os.path.isdir(filename):
            filename = os.path.join(filename, self.application.settings['default_html'])

        # return 404 if file does not exist or is a directory
        if not os.path.exists(filename):
            raise tornado.web.HTTPError(404)
        
        # load the file
        f = open(filename, 'r')
        s = f.read()
        f.close()

        # monkey patch in the websocket hooks
        if filename.endswith('.html'):
            monkeypatch_filename = os.path.join(os.path.dirname(__file__), 'monkey_patch.js')
            f = open(monkeypatch_filename, 'r')
            mps = f.read()
            f.close()
            s = s + '\n' + mps
        
        # serve the page
        self.write(s)
        

# --------------------------------------------------
#    Main
# --------------------------------------------------
def run(**kwargs):
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
    tornado.ioloop.PeriodicCallback(partial(callback_dispatcher, caller_globals), 1).start()
    IOLoop.current().start()


# if __name__ =='__main__':
#     # parse the args
#     parser = argparse.ArgumentParser(description='Serve a pylinkjs application')
# #    parser.add_argument('--nobrowser', type=int, help='do not auto launch the browser', default=False)    
#     parser.add_argument('--port', type=int, help='port to run server on', default=8300)
#     args = parser.parse_args()
#     run(vars(args))

