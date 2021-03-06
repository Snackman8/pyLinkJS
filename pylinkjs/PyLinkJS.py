# --------------------------------------------------
#    Imports
# --------------------------------------------------
import asyncio
import base64
import inspect
import json
import logging
import os
import queue
import random
import signal
import sys
import threading
import traceback
import time

import tornado.web
import tornado.websocket
from tornado.ioloop import IOLoop
from tornado.platform.asyncio import AnyThreadEventLoopPolicy


# --------------------------------------------------
#    Constants
# --------------------------------------------------
ALL_JSCLIENTS = []
RETVALS = {}


# --------------------------------------------------
#    Global Variables
# --------------------------------------------------
EXIT_EVENT = threading.Event()
INCOMING_PYCALLBACK_QUEUE = queue.Queue()
INCOMING_RETVAL_QUEUE = queue.Queue()
OUTGOING_EXECJS_QUEUE = queue.Queue()


# --------------------------------------------------
#    Functions
# --------------------------------------------------
def backtick_if_string(p):
    if type(p) == str:
        return "`%s`" % p
    else:
        return p


# --------------------------------------------------
#    Signal Handlers
# --------------------------------------------------
def signal_handler(_signum, _frame):
    EXIT_EVENT.set()
    exit()


# --------------------------------------------------
#    Classes
# --------------------------------------------------
class Code(object):
    def __init__(self, code):
        self.code = code


class PyLinkJQueryAttrWrapper(object):
    def __init__(self, htmlelementwrapper, attr):
        # set the attributes on the super() to avoid  __getattr__
        super().__setattr__('_htmlelementwrapper', htmlelementwrapper)
        super().__setattr__('_attr', attr)

    def __getattr__(self, attr):
        js = self._htmlelementwrapper._generate_selector_code()
        js += '.%s("%s")' % (self._attr, attr)
        return self._htmlelementwrapper._jsclient.eval_js_code(js)

    def __setattr__(self, attr, newval):
        js = self._htmlelementwrapper._generate_selector_code()
        if isinstance(newval, Code):
            js += '.%s("%s", %s)' % (self._attr, attr, newval.code)
        elif isinstance(newval, bool):
            js += '.%s("%s", %s)' % (self._attr, attr, {False: 'false', True: 'true'}[newval])
        elif isinstance(newval, int) or isinstance(newval, float):
            js += '.%s("%s", %s)' % (self._attr, attr, str(newval))
        else:
            js += '.%s("%s", %s)' % (self._attr, attr, backtick_if_string(newval))
        return self._htmlelementwrapper._jsclient.eval_js_code(js, blocking=False)


class PyLinkHTMLElementWrapper(object):
    def __init__(self, jsclient, selector):
        # set the attributes on the super() to avoid  __getattr__
        super().__setattr__('_jsclient', jsclient)
        super().__setattr__('_selector', selector)

    def _generate_selector_code(self):
        return """$('%s')""" % self._selector

    def __getattr__(self, attr):
        if attr in ('css', 'prop'):
            return PyLinkJQueryAttrWrapper(self, attr)

        js = self._generate_selector_code()
        js += '.%s()' % attr
        return self._jsclient.eval_js_code(js)

    def __setattr__(self, attr, newval):
        js = self._generate_selector_code()
        if isinstance(newval, Code):
            js += '.%s(%s)' % (attr, newval.code)
        else:
            js += '.%s(%s)' % (attr, backtick_if_string(newval))
        self._jsclient.eval_js_code(js, blocking=False)


class PyLinkJSClient(object):
    def __init__(self, websocket, thread_id):
        self._websocket = websocket
        self._thread_id = thread_id
        self.time_offset_ms = None
        self.event_time_ms = None
        self.tag = {}
        self.user = None

    def __getitem__(self, key):
        return PyLinkHTMLElementWrapper(self, key)

    def get_pathname(self):
        return '/' + self._websocket.request.path.partition('/')[2].partition('/')[2].partition('/')[2]

    def _send_eval_js_websocket_packet(self, js_id, js_code, send_return_value):
        pkt = {'id': js_id,
               'cmd': 'eval_js',
               'js_code': js_code,
               'send_return_value': send_return_value}
        if self._thread_id != threading.get_ident():
            IOLoop.instance().add_callback(self._websocket.write_message, json.dumps(pkt))
        else:
            self._websocket.write_message(json.dumps(pkt))

        return 0

    def get_broadcast_jscs(self):
        retval = []
        for jsc in self._websocket._all_jsclients.values():
            if jsc.get_pathname() == self.get_pathname():
                retval.append(jsc)
        return retval

    def browser_download(self, filename, filedata, blocking=False):
        filedata = filedata.encode('ascii')
        b64filedata = base64.b64encode(filedata).decode()
        js = """browser_download('%s', "%s");""" % (filename, b64filedata)
        self.eval_js_code(js, blocking)

    def eval_js_code(self, js_code, blocking=True):
        # init
        js_id = 'py_' + str(random.random())
        if blocking:
            evt = threading.Event()
        else:
            evt = None

        # put the javascript code on the EXECJS queue
        OUTGOING_EXECJS_QUEUE.put((self, evt, js_id, js_code))

        # if not blocking, just return
        if evt is None:
            return

        # wait for the return value then return
        evt.wait()
        retval = RETVALS[js_id][1]
        del RETVALS[js_id]
        return retval

    def select_add_option(self, select_selector, value, text):
        self.eval_js_code("""$('%s').append($('<option>', {value: '%s',text: '%s'}))""" % (select_selector, value,
                                                                                           text), blocking=False)

    def select_get_selected_option(self, select_selector):
        return self.eval_js_code("""$('%s').find(":selected").attr("value");""" % (select_selector))

    def select_set_selected_option(self, select_selector, option_value):
        """ select an option inside a HTML select element

            select_selector - jquery selector for the select element
            option_value - value of the option to select
        """
        self.eval_js_code("""$('%s option[value="%s"]').prop('selected', true)""" % (select_selector, option_value),
                          blocking=False)


# --------------------------------------------------
#    Thread Workers
# --------------------------------------------------
def heartbeat_threadworker(heartbeat_callback, heartbeat_interval):
    while True:
        time.sleep(heartbeat_interval)
        heartbeat_callback()


def start_execjs_handler_ioloop():
    async def coro_execjs_handler():
        # This coroutine runs in the EXECJS_HANDLER ioloop
        # handle when python code wants to send javascript code to browser
        while True:
            # exit if Ctrl-C
            if EXIT_EVENT.is_set():
                break

            # sleep if no incoming callbacks are available
            if OUTGOING_EXECJS_QUEUE.empty():
                await asyncio.sleep(0.001)
                continue

            jsclient, evt, js_id, js_code = OUTGOING_EXECJS_QUEUE.get()
            RETVALS[js_id] = (evt, None)

            jsclient._send_eval_js_websocket_packet(js_id, js_code, evt is not None)

    # thread to handle when python code wants to send javascript code to browser
    execjs_ioloop = asyncio.new_event_loop()
    execjs_ioloop.create_task(coro_execjs_handler())
    execjs_ioloop.run_forever()


def start_pycallback_handler_ioloop(caller_globals):
    # thread to handle calls when javascript wants to execute python code
    async def coro_pycallback_handler(caller_globals):
        # This coroutine runs in the PYCALLBACK_HANDLER ioloop
        # handle when javascript wants to execute python code
        while True:
            # exit if Ctrl-C
            if EXIT_EVENT.is_set():
                break

            # sleep if no incoming callbacks are available
            if INCOMING_PYCALLBACK_QUEUE.empty():
                await asyncio.sleep(0.001)
                continue

            jsc, js_data = INCOMING_PYCALLBACK_QUEUE.get()

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
                        func(jsc, *js_data['args'])
                    else:
                        if not js_data['no_error_if_undefined']:
                            s = 'No function found with name "%s"' % js_data['py_func_name']
                            js_code = """alert('%s');""" % s
                            jsc.eval_js_code(js_code)
                            raise Exception('No function found with name "%s"' % js_data['py_func_name'])
                except Exception:
                    sys.stderr.write(traceback.format_exc())

    # start the thread
    pycallbackhandler_ioloop = asyncio.new_event_loop()
    pycallbackhandler_ioloop.create_task(coro_pycallback_handler(caller_globals))
    pycallbackhandler_ioloop.run_forever()


def start_retval_handler_ioloop():
    # thread to handle calls when javascript wants to return a value back to python code
    async def coro_retval_handler():
        # This coroutine runs in the RETVAL_HANDLER ioloop
        # handle when javascript wants to return a value to python
        while True:
            # exit if Ctrl-C
            if EXIT_EVENT.is_set():
                break

            # sleep if no incoming callbacks are available
            if INCOMING_RETVAL_QUEUE.empty():
                await asyncio.sleep(0.001)
                continue

            _jsclient, caller_id, retval = INCOMING_RETVAL_QUEUE.get()
            evt, _ = RETVALS[caller_id]
            RETVALS[caller_id] = (evt, retval)
            if evt is not None:
                evt.set()

    retval_ioloop = asyncio.new_event_loop()
    retval_ioloop.create_task(coro_retval_handler())
    retval_ioloop.run_forever()


# --------------------------------------------------
#    Tornado Request Handlers
# --------------------------------------------------
class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")


class LoginHandler(tornado.web.RequestHandler):
    def get(self):
        filename = self.application.settings['login_html_page']
        with open(filename, 'r') as f:
            s = f.read()
        s = s.replace('{next_url}', self.request.headers.get('Referer', '/'))
        self.write(s)

    def post(self):
        self.set_secure_cookie("user", self.get_argument("name"))
        self.redirect(self.get_argument('next', '/'))


class LogoutHandler(tornado.web.RequestHandler):
    def get(self):
        self.clear_cookie("user")
        self.redirect(self.request.headers['Referer'])


class MainHandler(BaseHandler):
    def get(self):
        # strip off the leading slash, then combine with web directory
        filename = os.path.abspath(os.path.join(self.application.settings['html_dir'], self.request.path[1:]))

        # default to index.html if this is a directory
        if os.path.isdir(filename):
            filename = os.path.join(filename, self.application.settings['default_html'])

        # return 404 if file does not exist or is a directory
        if not os.path.exists(filename):
            if self.application.settings['on_404']:
                b = self.application.settings['on_404'](self.request.path[1:])
                if b is not None:
                    self.write(b)

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


class PyLinkJSWebSocketHandler(tornado.websocket.WebSocketHandler):
    def __init__(self, *args, **kwargs):
        self._all_jsclients = None
        self._jsc = None
        super().__init__(*args, **kwargs)

    def initialize(self, all_jsclients):
        self._all_jsclients = all_jsclients

    def open(self):
        # create a context
        self.set_nodelay(True)
        self._jsc = PyLinkJSClient(self, threading.get_ident())
        self._all_jsclients.append(self._jsc)
        if 'on_context_open' in self.application.settings:
            if self.application.settings['on_context_open'] is not None:
                self.application.settings['on_context_open'](self._jsc)

    def on_message(self, message):
        #        context_id = self.request.path
        js_data = json.loads(message)

        # correct the time between different client and server
        if js_data['cmd'] == 'synchronize_time':
            self._jsc.time_offset_ms = js_data['event_time_ms'] - time.time() * 1000

        self._jsc.event_time_ms = (js_data['event_time_ms'] - self._jsc.time_offset_ms)
        del js_data['event_time_ms']

        # put the packet in the queue
        if js_data['cmd'] == 'call_py':
            self._jsc.user = self.get_secure_cookie("user")
            INCOMING_PYCALLBACK_QUEUE.put((self._jsc, js_data), True, None)

        if js_data['cmd'] == 'return_py':
            INCOMING_RETVAL_QUEUE.put((self._jsc, js_data['caller_id'], js_data.get('retval', None)), True, None)

    def on_close(self):
        # clean up the context
        #        context_id = self.request.path
        print('websocket closed!')
        if 'on_context_close' in self.application.settings:
            if self.application.settings['on_context_close'] is not None:
                self.application.settings['on_context_close'](self._jsc)
        self._all_jsclients.remove(self._jsc)
        del self._jsc


# --------------------------------------------------
#    Functions
# --------------------------------------------------
def get_broadcast_jsclients(pathname):
    retval = []
    for jsc in ALL_JSCLIENTS:
        if jsc.get_pathname() == pathname:
            retval.append(jsc)
    return retval


def get_all_jsclients():
    return ALL_JSCLIENTS


# --------------------------------------------------
#    Main
# --------------------------------------------------
def run_pylinkjs_app(**kwargs):
    # exit on Ctrl-C
    signal.signal(signal.SIGINT, signal_handler)

    if 'port' not in kwargs:
        kwargs['port'] = 8300
    if 'default_html' not in kwargs:
        kwargs['default_html'] = 'index.html'
    if 'html_dir' not in kwargs:
        kwargs['html_dir'] = '.'
    if 'login_html_page' not in kwargs:
        kwargs['login_html_page'] = os.path.join(os.path.dirname(__file__), 'login.html')
    if 'cookie_secret' not in kwargs:
        logging.warning('COOKIE SECRET IS INSECURE!  PLEASE CHANGE')
        kwargs['cookie_secret'] = 'GENERIC COOKIE SECRET'
    if 'heartbeat_callback' not in kwargs:
        kwargs['heartbeat_callback'] = None
    if 'heartbeat_interval' not in kwargs:
        kwargs['heartbeat_interval'] = None
    if 'login_handler' not in kwargs:
        kwargs['login_handler'] = LoginHandler
    if 'logout_handler' not in kwargs:
        kwargs['logout_handler'] = LogoutHandler
    if 'extra_settings' not in kwargs:
        kwargs['extra_settings'] = {}

    asyncio.set_event_loop_policy(AnyThreadEventLoopPolicy())

    request_handlers = [
        (r"/websocket/.*", PyLinkJSWebSocketHandler, {'all_jsclients': ALL_JSCLIENTS}),
        (r"/login", kwargs['login_handler']),
        (r"/logout", kwargs['logout_handler']),
        (r"/.*", MainHandler), ]

    app = tornado.web.Application(
        request_handlers,
        default_html=kwargs['default_html'],
        html_dir=kwargs['html_dir'],
        login_html_page=kwargs['login_html_page'],
        cookie_secret=kwargs['cookie_secret'],
        on_404=kwargs.get('on_404', None),
        **kwargs['extra_settings']
    )

    caller_globals = inspect.stack()[1][0].f_globals

    # start additional ioloops on new threads
    threading.Thread(target=start_pycallback_handler_ioloop, args=(caller_globals,), daemon=True).start()
    threading.Thread(target=start_retval_handler_ioloop, args=(), daemon=True).start()
    threading.Thread(target=start_execjs_handler_ioloop, args=(), daemon=True).start()
    if kwargs['heartbeat_interval']:
        threading.Thread(target=heartbeat_threadworker, args=(kwargs['heartbeat_callback'], kwargs['heartbeat_interval']), daemon=True).start()

    # start the tornado server
    app.listen(kwargs['port'])
    app.settings['on_context_close'] = kwargs.get('onContextClose', None)
    app.settings['on_context_open'] = kwargs.get('onContextOpen', None)
    logging.info('**** Starting app on port %d' % kwargs['port'])
    IOLoop.current().start()
