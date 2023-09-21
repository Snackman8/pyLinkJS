""" pylinkjs library """

# --------------------------------------------------
#    Imports
# --------------------------------------------------
import asyncio
import base64
from  functools import partial
import importlib
import inspect
import json
import logging
from multiprocessing import Process, Queue
import os
import queue
import random
import shutil
import signal
import subprocess
import sys
import threading
import traceback
import time
import uuid
from types import ModuleType

import tornado.template
import tornado.web
import tornado.websocket
from tornado.ioloop import IOLoop
from tornado.platform.asyncio import AnyThreadEventLoopPolicy
from tornado.websocket import WebSocketClosedError
from playwright.sync_api import sync_playwright


# --------------------------------------------------
#    Constants
# --------------------------------------------------
ALL_JSCLIENTS = []
RETVALS = {}
DEFAULT_PRINT_TIMEOUT = 10
INITIAL_JSC_MAPPINGS = {}


# --------------------------------------------------
#    Global Variables
# --------------------------------------------------
EXIT_EVENT = threading.Event()
INCOMING_PYCALLBACK_QUEUE = queue.Queue()
INCOMING_RETVAL_QUEUE = queue.Queue()
OUTGOING_EXECJS_QUEUE = queue.Queue()
INTERNAL_POLLING_INTERVAL = 0.015

# --------------------------------------------------
#    Functions
# --------------------------------------------------
def backtick_if_string(p):
    if type(p) == str:
        # special case for backslash
        p = p.replace('\\', '\\\\')
        return "`%s`" % p
    else:
        return p


def print_url(url, output_type, timeout=None, orientation='landscape', force_scale=None, force_fit=False, extra_delay=1):
    """
        print url to pdf.

        The renderer will autoscale between 96pi to 144dpi to automatically fill the page width

        Args:
            url - url to print
            output_type - pdf or png, default is pdf
            timeout - number of seconds to wait for page to complete before printing, default is 5
            orientation - landscape or portrait.  Default is landscape
            force_scale - scale to force printing at, default is None
            force_fit - force printout scaling to fit width to page
            extra_delay - extra time to add after web page is rendering to allow rendering to complete, default is 1
    """
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(url)

            if timeout is None:
                try:
                    print_timeout = page.evaluate('''() => HINT_PRINT_TIMEOUT''')
                    timeout = print_timeout
                    print(f'USING OVERIDE PRINT TIMEOUT OF {timeout} seconds')
                except:
                    timeout = DEFAULT_PRINT_TIMEOUT
                    print(f'USING TIMEOUT OF {timeout} seconds')

            # wait for page to load
            start_time = time.time()
            while (time.time() - start_time) < int(timeout):
                time.sleep(1)
                try:
                    ready_finished = page.evaluate('''() => ready_finished''')
                    if ready_finished:
                        print('READY!')
                        if INCOMING_PYCALLBACK_QUEUE.empty() and INCOMING_RETVAL_QUEUE.empty() and OUTGOING_EXECJS_QUEUE.empty():
                            print('QUEUES EMPTY')
                            try:
                                page_ready = page.evaluate('''() => HINT_PRINT_PAGE_READY''')
                                if page_ready == 1:
                                    print('HINT_PRINT_PAGE_READY')
                                    break
                            except:
                                print('HINT_PRINT_PAGE_READY NOT PRESENT')
                except:
                    pass
            time.sleep(int(extra_delay))

            # handle png
            if output_type == 'png':
                return page.screenshot(full_page=True), 'image/png'

            # calculate if force_fit
            if force_fit:
                # get the dimensions
                dimensions = page.evaluate('''() => {
                    return {
                        width: document.body.scrollWidth,
                        height: document.body.scrollHeight,
                        deviceScaleFactor: window.devicePixelRatio, }}''')

                # calculate the scale factor
                if orientation == 'landscape':
                    force_scale = 1584 / dimensions['width']
                else:
                    force_scale = 1224 / dimensions['width']

            # save to pdf
            if force_scale:
                pdf_bytes = page.pdf(landscape=(orientation == 'landscape'), scale=force_scale)
            else:
                pdf_bytes = page.pdf(landscape=(orientation == 'landscape'))
            return pdf_bytes, 'application/pdf; charset="utf-8"'
    except Exception as e:
        traceback.print_exc()
        print(e)


def search_for_magic_function(func_name):
    try:
        frames = []
        cf = inspect.currentframe()

        while cf is not None:
            # handle circular references
            if cf in frames:
                break
            frames.append(cf)

            # look for the function name
            cf_name = cf.f_globals['__name__']
            m = sys.modules[cf_name]
            if hasattr(m, func_name):
                f = getattr(m, func_name)
                if callable(f):
                    return f

            # move up
            cf = cf.f_back
    finally:
        for f in frames:
            del f


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
    def __init__(self, websocket, jsc_id, thread_id, extra_settings):
        """ init """
        self._websocket = websocket
        self._jsc_id = jsc_id
        # jsc sequence number 0 is shared with template creation
        self._sequence_number = 0
        self._thread_id = thread_id
        self.time_offset_ms = None
        self.event_time_ms = None
        self.tag = extra_settings.copy()
        self._tornado_ioloop = IOLoop.current()
        self.user = None

    def __getattr__(self, key):
        """ if the attribute does not exist intrinsicly on this instance, search the plugins for exposed functions
            which match the attribute name

            Args:
                key - name of the function

            Returns:
                the function which is exposed by a plugin
        """
        plugins = self._websocket.application.settings.get('plugins', [])
        for p in plugins:
            jsc_exposed_funcs = getattr(p, 'jsc_exposed_funcs', [])
            if key in jsc_exposed_funcs:
                return partial(jsc_exposed_funcs[key], self)

        raise AttributeError(key)

    def __getitem__(self, key):
        return PyLinkHTMLElementWrapper(self, key)

    def get_setting(self, setting_name):
        """ return a setting that was passed into the application on startup

            Args:
                setting_name - name of the setting to return

            Returns:
                setting value
        """
        return self._websocket.application.settings.get(setting_name, None)

    def get_pathname(self):
        """ return the path portion of the url of the browser bound to the JSClient instance

            For example, if the url of the JSClient is http://www.test.com/origin?query=a then this
            function would return /origin
        """
        return '/' + self._websocket.request.path.partition('/')[2].partition('/')[2].partition('/')[2]

    def _send_eval_js_websocket_packet(self, js_id, js_code, send_return_value):
        # throw exception of websocket is closed
        if self._websocket.close_code is not None:
            raise WebSocketClosedError()

        pkt = {'id': js_id,
               'cmd': 'eval_js',
               'js_code': js_code,
               'send_return_value': send_return_value}
        if self._thread_id != threading.get_ident():
            self._tornado_ioloop.add_callback(self._websocket_write_message_callback, js_id, json.dumps(pkt))
        else:
            self._websocket.write_message(json.dumps(pkt))

        return 0

    def _websocket_write_message_callback(self, js_id, data):
        try:
            self._websocket.write_message(data)
        except Exception as e:
            if js_id in RETVALS:
                if RETVALS[js_id][0]:
                    RETVALS[js_id][0].set()
            if e.__class__ == WebSocketClosedError:
                logging.info('********** Detect websocket closed in callback')
            else:
                raise(e)

    def get_broadcast_jscs(self):
        """ return all JSClient instances known by this server """
        retval = []
        for jsc in self._websocket._all_jsclients.values():
            if jsc.get_pathname() == self.get_pathname():
                retval.append(jsc)
        return retval

    def browser_download(self, filename, filedata, blocking=False):
        """ download a file from the backend to the users computer through the browser

            filename - the default name of the file to save as
            filedata - the binary data of the file to download
            blocking - if True, then this function will not return until the file has completed downloading
        """
        filedata = filedata.encode('ascii')
        b64filedata = base64.b64encode(filedata).decode()
        js = """browser_download('%s', "%s");""" % (filename, b64filedata)
        self.eval_js_code(js, blocking)

    def eval_js_code(self, js_code, blocking=True):
        """ request that the browser evaluate javascript code

            js_code - the javascript code to execute
            blocking - if True, this function will not return until the javascript has completed execution

            Returns:
                the data that the executed javascript evaluates to
        """
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
        evt.wait(timeout=1.0)
        retval = None
        if js_id in RETVALS:
            retval = RETVALS[js_id][1]
            del RETVALS[js_id]
        return retval

    def get_id(self):
        return self._jsc_id

    def get_sequence_number(self):
        return self._sequence_number

    def increment_sequence_number(self):
        """ incremenet the jsc sequence number
            the sequence number is useful for data caching for separate data fetches happening in the same request
        """
        self._sequence_number = self._sequence_number + 1

    def modal_alert(self, title, body, callback=''):
        """ Shows a modal alert dialog with an OK button

            Args:
                title - html title to show in the modal dialog
                body - html body to show in the modal dialog
                callback - callback in string form for when the OK buttion is clicked,
                           i.e. onclick="call_py('btn_clicked', 'create_new_item_save');"
        """
        self.modal_new(title=f"""<span class=text-danger>{title}</span>""",
                      body=body,
                      buttons=[{'text': 'OK', 'classes': 'btn-primary',
                                'attributes': f"""data-bs-dismiss="modal" {callback} """}])

    def modal_confirm(self, title, body, callback=''):
        """ Shows a modal confirm dialog with OK and Cancel buttons

            Args:
                title - html title to show in the modal dialog
                body - html body to show in the confirm dialog
                callback - callback in string form for when the OK buttion is clicked,
                           i.e. onclick="call_py('btn_clicked', 'create_new_item_save');"
        """
        self.modal_new(title=f"""<span class=text-danger>{title}</span>""",
                      body=body,
                      buttons=[{'text': 'Cancel', 'classes': 'btn-secondary', 'attributes': 'data-bs-dismiss="modal"'},
                               {'text': 'OK', 'classes': 'btn-danger',
                                'attributes': f"""data-bs-dismiss="modal" {callback} """}])

    def modal_input(self, title, hint, callback=''):
        """ Shows a modal input dialog where the user can input text

            Args:
                title - title to show in the modal dialog
                hint - hint text to show in the input box before the user begins typing
                callback - callback in string form for when the OK buttion is clicked,
                           i.e. onclick="call_py('btn_clicked', 'create_new_item_save');"

            Returns:
                text from the input box of the last shown modal input
        """
        self.modal_new(title=title,
                      body=f"""<div class="form-group">
                                   <input class="form-control" id="modal_input" placeholder="{hint}"  autocomplete="off">
                               </div>""",
                      buttons=[{'text': 'Cancel', 'classes': 'btn-secondary', 'attributes': 'data-bs-dismiss="modal"'},
                               {'text': 'OK', 'classes': 'btn-primary', 'attributes': 'data-bs-dismiss="modal" ' + callback}])

    def modal_input_get_text(self):
        """ return the text from the last modal_input

            Returns:
                text from the input box of the last shown modal input
        """
        return self.eval_js_code('$("#modal_input").val()')

    def modal_new(self, title, body, buttons, modal_id='jsclient_modal', autoshow=True):
        """ create a new modal popup dialog

            Args:
                title - html to place in the title of the modal
                body - html to place in the body of the modal
                buttons - list of button dictionaries with the attributes below
                            attributes - additional attributes for the button element
                            classes - additional classes for the button
                            text - text of the button
                          i.e. [{'text': 'Cancel', 'classes': 'btn-secondary', 'attributes': 'data-bs-dismiss="modal"'},
                                {'text': 'OK', 'classes': 'btn-primary', 'attributes': 'onclick="call_py("btn_clicked", "ok_button")'}])
                modal_id - id of the modal to create
                autoshow - if True, this modal will be automatically shown, if False, an explicit call to modal_show is needed to show this modal
        """
        # generate the html for the buttons
        html_buttons = ''
        for x in buttons:
            html_buttons = html_buttons + f"""<button type="button" class="btn {x.get('classes')}" {x.get('attributes')}>{x.get('text', '')}</button>"""

        # delete existing modal if present
        js = f"""
            $('#{modal_id}').remove();
            $(document.body).append(`
                <div class="modal fade" id={modal_id} data-bs-backdrop="static" data-bs-keyboard="false" tabindex="-1">
                    <div class="modal-dialog modal-dialog-centered">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">{title}</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">{body}</div>
                            <div class="modal-footer">
                                {html_buttons}
                            </div>
                        </div>
                    </div>
                </div>`);
        """

        # append a new modal
        self.eval_js_code(js)

        # autoshow
        if autoshow:
            self.modal_show(modal_id)

    def modal_show(self, modal_id='jsclient_modal'):
        """ show a modal created with the modal_new function

            Args:
                modal_id - id of the modal to show
        """
        self.eval_js_code(f"""$('#{modal_id}').modal('show')""")

    def select_get_options(self, select_selector):
        """ retrieve the value / text pair of each option in the selector

            Args:
                select_selector - jquery selector for the select element

            Returns:
                list of options.  each option is a two element list, first element is the value, second element is the text
                i.e. [['value_a', 'text_a'], ['value_b', 'text_b']]
        """
        js = f"""$('{select_selector} option').map(function(){{return [[$(this).attr("value"), $(this).html()]]}}).get()"""
        return self.eval_js_code(js)

    def select_get_selected_options(self, select_selector):
        """ retrieve the selected options

            Args:
                select_selector - jquery selector for the select element

            Returns:
                list of selected options.  each option is a two element list, first element is the value, second element is the text
                i.e. [['value_a', 'text_a'], ['value_b', 'text_b']]
        """
        js = f"""$('{select_selector} :selected').map(function(){{return [[$(this).attr("value"), $(this).html()]]}}).get()"""
        return self.eval_js_code(js)

    def select_set_options(self, select_selector, new_options):
        """ replaces all the options in the select with new options

            Args:
                select_selector - jquery selector for the select element
                new_options - list of new options, each option is a two element list of value and text, i.e. [['value_a', 'text_a'], ['value_b', 'text_b']]
        """
        # convert if new_options is a single list
        new_options2 = []
        for x in new_options:
            if (type(x) is not list) and (type(x) is not tuple):
                x = [x, x]
            new_options2.append(x)

        # convert tuples to lists for javascript
        new_options = [list(x) for x in new_options2]

        js = f"""$('{select_selector}').empty();
                 $.each({new_options}, function(key, value) {{
                     $('{select_selector}').append($("<option></option>")
                        .attr("value", value[0]).text(value[1]));
                 }})

        """
        return self.eval_js_code(js)

    def select_set_selected_options(self, select_selector, option_values):
        """ selectes options in the select

            Args:
                select_selector - jquery selector for the select element
                option_values - list of options values to select to a single value to select
        """
        if type(option_values) is not list:
            option_values = [option_values]
        js = f"""$('{select_selector}').val({option_values})"""
        return self.eval_js_code(js)


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
                await asyncio.sleep(INTERNAL_POLLING_INTERVAL)
                continue

            jsclient, evt, js_id, js_code = OUTGOING_EXECJS_QUEUE.get()
            RETVALS[js_id] = (evt, None)

            try:
                jsclient._send_eval_js_websocket_packet(js_id, js_code, evt is not None)
            except Exception as e:
                if js_id in RETVALS:
                    if RETVALS[js_id][0]:
                        RETVALS[js_id][0].set()
                if e.__class__ == WebSocketClosedError:
                    logging.info('********** Detect websocket closed in callback')
                else:
                    logging.info(f'pylinkjs: exception coro_execjs_handler')
                    logging.exception(e)

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
                await asyncio.sleep(INTERNAL_POLLING_INTERVAL)
                continue

            jsc, js_data = INCOMING_PYCALLBACK_QUEUE.get()

            if js_data['cmd'] == 'call_py':
                try:
                    # prepend module path if this is a subdirectory
                    subdir = js_data['window_location_pathname']
                    if subdir.endswith('.html'):
                        subdir = subdir[:-5]
                    else:
                        # this is an apache rewrite, so we need to skip the first path portion
                        subdir = '/'.join(subdir.split('/').pop(0))
                    subdir = subdir.replace('/', '.')[1:]
                    if subdir != '':
                        fullfuncpath = subdir + '.' + js_data['py_func_name']
                    else:
                        fullfuncpath = js_data['py_func_name']
                    
                    # split the function into modules and function name
                    parts = fullfuncpath.split('.')

                    # init the search space
                    new_search_space = [caller_globals, locals(), globals()]

                    # search through the search space
                    for p in parts:
                        # init the search_space and new_search_space
                        search_space, new_search_space = new_search_space, None

                        # abandon if we have no search space
                        if search_space is None:
                            break

                        # search for the next level
                        for ss in search_space:
                            if isinstance(ss, ModuleType):
                                if hasattr(ss, p):
                                    new_search_space = [getattr(ss, p)]
                            else:
                                if p in ss:
                                    new_search_space = [ss[p]]
                                    break

                    # perform a hail mary
                    if new_search_space is None:
                        try:
                            m = importlib.import_module(subdir)
                            if hasattr(m, js_data['py_func_name']):
                                new_search_space = [getattr(m, js_data['py_func_name'])]
                        except Exception as e:
                            pass                    
                        
                    # error if nothing was found in the final new_search_space
                    if new_search_space is None:
                        # check if we should emit this error or not
                        if not js_data.get('no_error_if_undefined', False):
                            s = 'No function found with name "%s"' % js_data['py_func_name']
                            js_code = """alert('%s');""" % s
                            jsc.eval_js_code(js_code)
                    else:
                        # call the function
                        func = new_search_space[0]
                        if not js_data.get('new_thread', False):
                            func(jsc, *js_data['args'])
                        else:
                            t = threading.Thread(target=lambda func, jsc, args: func(jsc, *args), args=(func, jsc, js_data['args']))
                            t.start()
                except Exception as e:
                    sys.stderr.write(traceback.format_exc())
                    js_code = """alert("%s");""" % str(e)
                    print(js_code)
                    jsc.eval_js_code(js_code)

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
                await asyncio.sleep(INTERNAL_POLLING_INTERVAL)
                continue

            _jsclient, caller_id, retval = INCOMING_RETVAL_QUEUE.get()
            if caller_id in RETVALS:
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
    def print_thread_worker(self, url, print_output_type='pdf', print_timeout=None, print_orientation='landscape', print_force_scale=None, print_force_fit=False,
                            print_extra_delay=1):
        print_bytes, content_type = print_url(url=url, output_type=print_output_type, timeout=print_timeout,
                                              orientation=print_orientation, force_scale=print_force_scale,
                                              force_fit=print_force_fit, extra_delay=print_extra_delay)
        self.set_header("Content-Type", content_type)
        self.set_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.write(print_bytes)
        self.finish()

    async def get(self):
        self._auto_finish = False

        # strip off the leading slash, then combine with web directory
        filename = os.path.abspath(os.path.join(self.application.settings['html_dir'], self.request.path[1:]))

        # default to index.html if this is a directory
        if os.path.isdir(filename):
            dirname = filename
            filename = os.path.join(dirname, self.application.settings['default_html'])
            # if not os.path.exists(filename):
            #     filename_index = os.path.join(dirname, 'index.html')
            #     if os.path.exists(filename_index):
            #         filename = filename_index

        # return 404 if file does not exist or is a directory
        if not os.path.exists(filename):
            if self.application.settings['on_404']:
                handle_result = await IOLoop.current().run_in_executor(None, self.application.settings['on_404'], self.request.path[1:],
                                                                       self.request.uri, self.request.headers['host'], self.settings['extra_settings'])
                if handle_result is not None:
                    html, content_type, status_code = handle_result
                    if html is not None:
                        self.write(html)
                    if content_type is not None:
                        self.set_header("Content-Type", f'{content_type}; charset="utf-8"')
                    if status_code is not None:
                        self.set_status(status_code)
                        self.finish()
                    return
                else:
                    raise tornado.web.HTTPError(404)
            else:
                raise tornado.web.HTTPError(404)

        # load the file
        f = open(filename, 'rb')
        b = f.read()
        f.close()

        # monkey patch in the websocket hooks
        if filename.endswith('.html'):
            if 'output' in self.request.query_arguments:
                if self.request.query_arguments.get('output', '')[0].lower() in [b'pdf', b'png']:
                    # build and remove pdf_arguments
                    pdf_kwargs = {}
                    uri = self.request.uri
                    for name in ['output', 'print_timeout', 'print_orientation', 'print_force_scale', 'print_force_fit', 'print_extra_delay']:
                        if name in self.request.query_arguments:
                            pdf_kwargs[name] = self.request.query_arguments[name][0].decode()
                            uri = uri.replace(f'{name}={pdf_kwargs[name]}', '')
                    url = self.request.protocol + "://" + self.request.host + uri

                    # special handling for apache rewrite proxy
                    if 'X-Forwarded-Host' in self.request.headers:
                        url = self.request.protocol + "://" + self.request.host + ':' + str(self.application.settings['port']) + uri

                    pdf_kwargs['url'] = url
                    pdf_kwargs['print_output_type'] = pdf_kwargs['output']
                    del pdf_kwargs['output']

                    # print to pdf in another thread
                    t = threading.Thread(target=self.print_thread_worker, kwargs=pdf_kwargs)
                    t.start()
                    return

            monkeypatch_filename = os.path.join(os.path.dirname(__file__), 'monkey_patch.js')
            f = open(monkeypatch_filename, 'rb')
            mps = f.read()
            f.close()
            b = b + b'\n' + mps

            for p in self.settings['plugins']:
                if hasattr(p, 'inject_javascript'):
                    b = b + b'\n<script>\n' + p.inject_javascript() + b'\n</script>\n'

            t = tornado.template.Template(b)
            template_vars = self.application.settings.get('global_template_vars', {})
            template_vars['request_path'] = self.request.path
            template_vars['jsc_id'] = '0.' + str(uuid.uuid4())
            template_vars['page_instance_id'] = '0.' + str(uuid.uuid4())
            template_vars['jsc_sequence_number'] = 0
            INITIAL_JSC_MAPPINGS[template_vars['jsc_id']] = template_vars['page_instance_id']
            self.write(t.generate(**template_vars))
            self.finish()
            return

        # apply proper mime type for css
        if filename.endswith('.css'):
            self.set_header("Content-Type", 'text/css; charset="utf-8"')

        # apply proper mime type for js
        if filename.endswith('.js'):
            self.set_header("Content-Type", 'text/javascript; charset="utf-8"')

        # apply proper mime type for js
        if filename.endswith('.svg'):
            self.set_header("Content-Type", 'image/svg+xml')

        # apply proper mime type for js
        if filename.endswith('.png'):
            self.set_header("Content-Type", 'image/png')

        # apply proper mime type for js
        if filename.endswith('.jpg'):
            self.set_header("Content-Type", 'image/jpg')

        # serve the page
        self.write(b)
        self.finish()


class PyLinkJSWebSocketHandler(tornado.websocket.WebSocketHandler):
    def __init__(self, *args, **kwargs):
        self._all_jsclients = None
        self._jsc = None
        super().__init__(*args, **kwargs)

    def initialize(self, all_jsclients):
        self._all_jsclients = all_jsclients

    def open(self):
        # create a context
        remote_ip = self.request.headers.get("X-Real-IP") or self.request.headers.get("X-Forwarded-For") or self.request.remote_ip
        logging.info(f'pylinkjs: websocket connect {remote_ip}')
        self.set_nodelay(True)
        jsc_id = self.request.uri.split('/')[2]
        self._jsc = PyLinkJSClient(self, jsc_id, threading.get_ident(), self.application.settings['extra_settings'])
        self._jsc.page_instance_id = INITIAL_JSC_MAPPINGS.get(jsc_id, None)
        self._all_jsclients.append(self._jsc)
        for func in self.application.settings['on_context_open']:
            func(self._jsc)

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
            props = ['user_auth_username', 'user_auth_method']
            for p in props:
                setattr(self._jsc, p, self.get_secure_cookie(p))
                if getattr(self._jsc, p) is not None:
                    setattr(self._jsc, p, getattr(self._jsc, p).decode())
            INCOMING_PYCALLBACK_QUEUE.put((self._jsc, js_data), True, None)

        if js_data['cmd'] == 'return_py':
            INCOMING_RETVAL_QUEUE.put((self._jsc, js_data['caller_id'], js_data.get('retval', None)), True, None)

    def on_close(self):
        # clean up the context
        remote_ip = self.request.headers.get("X-Real-IP") or self.request.headers.get("X-Forwarded-For") or self.request.remote_ip
        logging.info(f'pylinkjs: websocket close {remote_ip}')

        for func in self.application.settings['on_context_close']:
            func(self._jsc)
        self._all_jsclients.remove(self._jsc)
        del self._jsc


# --------------------------------------------------
#    Functions
# --------------------------------------------------
def _mp_wrapper(func, args, kwargs, q):
    retval = func(*args, **kwargs)
    q.put(retval)


def execute_in_subprocess(func, *args, **kwargs):
    q = Queue()
    p = Process(target=_mp_wrapper, args=(func, args, kwargs, q))
    p.start()
    retval = q.get()
    p.join()
    return retval


def get_broadcast_jsclients(pathname):
    """ return all JSClient instances known by this server filtered by the pathname

        pathname - the pathname to filter by, i.e. /

        Returns
            a list of JSClient instances with the correct pathname
    """
    retval = []
    for jsc in ALL_JSCLIENTS:
        if jsc.get_pathname() == pathname:
            retval.append(jsc)
    return retval


def get_all_jsclients():
    """ return all JSClient instances known by this server

        Returns
            a list of JSClient instances
     """
    return ALL_JSCLIENTS


# --------------------------------------------------
#    Main
# --------------------------------------------------
def run_pylinkjs_app(**kwargs):
    """ this function runs a pylinkjs application

        Note: The extra settings are available in the application.settings and in the jsc.tags

        port - port number to run application on, default is 8300
        default_html - filename for the default html file, defaults to index.html
        html_dir - directory containing html files, defaults to .
        login_html_page - filename for the default login html page, defaults to prepackaged login.html
        cookie_secret - secret cookie string, please set this to a random string
        heartbeat_callback - heartbeat function name which will be called periodically, defaults to None
        heartbeat_interval - interval in seconds when the heartbeat_callback function will be called, defaults to None
        login_handler - tornado handler for login, defaults to built in Login Handler
        logout_handler - tornado handler for login, defaults to built in Logout Handler
        extra_settings - dictionary of properties that will be loaded into the tag property of the jsc client
        on_404 - handler if a URL does not have a matching .html file.  Allows dynamic generation of pages
        app_mode - if True, enables single page app mode, default is False
        app_top - position in pixels for the top of the application
        app_left - position in pixels for the left of the application
        app_height - position in pixels for the height of the application
        app_width - position in pixels for the width of the application
        onQueryTemplateVariables - handler to provide variables for the template before rendering
        internal_polling_interval - internal polling interval, decrease for less cpu usage with higher latency.  default is 0.015 seconds
        **kwargs - additional named arguments will be placed into the settings property of the tornado app but will not be available to the jsc context
    """

    global INTERNAL_POLLING_INTERVAL

    # exit on Ctrl-C
    try:
        signal.signal(signal.SIGINT, signal_handler)
    except ValueError:
        pass

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
    if 'logout_post_action_url' not in kwargs:
        kwargs['logout_post_action_url'] = '/'

    if 'extra_settings' not in kwargs:
        kwargs['extra_settings'] = {}

    if 'app_top' not in kwargs:
        kwargs['app_top'] = 0
    if 'app_left' not in kwargs:
        kwargs['app_left'] = 0
    if 'app_height' not in kwargs:
        kwargs['app_height'] = 400
    if 'app_width' not in kwargs:
        kwargs['app_width'] = 800
    if 'app_mode' not in kwargs:
        kwargs['app_mode'] = False

    if 'internal_polling_interval' not in kwargs:
        kwargs['internal_polling_interval'] = 0.015

    kwargs['plugins'] = kwargs.get('plugins', [])

    INTERNAL_POLLING_INTERVAL = kwargs['internal_polling_interval']

    # load the plugins
    for plugin in kwargs['plugins']:
        plugin.register(kwargs)

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
        extra_settings=kwargs['extra_settings']
    )

    caller_globals = inspect.stack()[1][0].f_globals

    # start additional ioloops on new threads
    threading.Thread(target=start_pycallback_handler_ioloop, args=(caller_globals,), daemon=True).start()
    threading.Thread(target=start_retval_handler_ioloop, args=(), daemon=True).start()
    threading.Thread(target=start_execjs_handler_ioloop, args=(), daemon=True).start()
    if kwargs['heartbeat_interval']:
        threading.Thread(target=heartbeat_threadworker, args=(kwargs['heartbeat_callback'], kwargs['heartbeat_interval']), daemon=True).start()

    # handle magic functions
    for magic_func_name in ['on_context_close', 'on_context_open']:
        app.settings[magic_func_name] = []
        if magic_func_name in kwargs:
            app.settings[magic_func_name].append(kwargs.get[magic_func_name])
        else:
            if (func := search_for_magic_function(magic_func_name)):
                app.settings[magic_func_name].append(func)

        for plugin in kwargs['plugins']:
            if hasattr(plugin, magic_func_name):
                app.settings[magic_func_name].append(getattr(plugin, magic_func_name))

    # start the tornado server
    server = app.listen(kwargs['port'], xheaders=True)
    for k, v in kwargs.items():
        app.settings[k] = v

    logging.info('**** Starting app on port %d' % kwargs['port'])
    eventLoopThread = threading.Thread(target=IOLoop.current().start)
    eventLoopThread.daemon = True
    eventLoopThread.start()

    # launch the browser if needed
    if kwargs['app_mode']:
        logging.info('Starting app mode')
        top = kwargs['app_top']
        left = kwargs['app_left']
        width = kwargs['app_width']
        height = kwargs['app_height']
        url = f"http://localhost:{kwargs['port']}"
        exe = shutil.which('chromium')
        my_env = os.environ.copy()
        my_env["XAUTHORITY"] = os.path.expanduser('~/.Xauthority')
        p = subprocess.Popen(f'{exe} --window-size="{width},{height}" --window-position="{left},{top}" --user-data-dir="/tmp/{time.time()}" --app={url} ',
                             env=my_env, close_fds=True, start_new_session=True, shell=True)

        while p.poll() is None:
            time.sleep(1)

        # terminate all ioloops
        EXIT_EVENT.set()
        server.stop()
        IOLoop.instance().stop()
    else:
        while True:
            time.sleep(1)
