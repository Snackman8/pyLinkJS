# pyLinkJS
Simple bridge to allow Python to communicate with JavaScript

### Table of Contents

**[Installation](#installation)**<br>
**[Basic Example](#basic-example)**<br>
**[Documentation](#documentation)**<br>
[&nbsp;&nbsp;&nbsp;&nbsp;Event Handlers](#event-handlers)<br>
[&nbsp;&nbsp;&nbsp;&nbsp;PyLinkJS](#pylinkjs-1)<br>
[&nbsp;&nbsp;&nbsp;&nbsp;JSClient (Core Methods)](#jsclient-core-methods)<br>
[&nbsp;&nbsp;&nbsp;&nbsp;JSClient (Modal UI Methods)](#jsclient-modal-ui-methods)<br>
[&nbsp;&nbsp;&nbsp;&nbsp;JSClient (Select Element Methods)](#jsclient-select-element-methods)<br>
[&nbsp;&nbsp;&nbsp;&nbsp;PNG/PDF Output](#png-pdf-output)<br>
**[Useful Code Examples](#useful-code-examples)**<br>
**[Apache2 Reverse Proxy](#to-use-pylinkjs-behind-an-apache-reverse-proxy-subdirectory-foo)**<br>

## Installation

The easiest way to install is to clone this repository to your home directory and then pip3 install
```
sudo pip3 install git+https://github.com/Snackman8/pyLinkJS

or

cd ~
git clone https://github.com/Snackman8/pyLinkJS
cd pyLinkJS
sudo pip3 install .
```

## Basic Example

To create a simple PylinkJS example, follow these steps to set up the example.py, example.html, and example2.html files:

**File: example.py**

_This Python file defines a function button_clicked that updates an HTML element in response to a button click on the web page._
```python
import logging
import datetime
from pylinkjs.PyLinkJS import run_pylinkjs_app, Code

def button_clicked(jsc, a, b):
    """
    Handles button click events, updating the webpage's HTML and styles.

    Parameters:
    -----------
    jsc : javascript_context
        The JavaScript context for the current session, used to interact with page elements.
    a, b : any
        Dummy parameters to demonstrate passing data from JavaScript to Python.

    JavaScript Example:
    -------------------
    call_py('button_clicked', 'param1', 'param2');
    """
    jsc['#divout'].html = "Current Time: " + datetime.datetime.now().strftime('%H:%M:%S')
    jsc['#divout'].css.color = 'red'
    jsc['#divout'].click = Code('function() { alert("AA"); }')


# start the thread and the app
logging.basicConfig(level=logging.DEBUG, format='%(relativeCreated)6d %(threadName)s %(message)s')

# Starts the PylinkJS app serving `example.html` on `localhost:8300` (default port) for browser-Python interaction.
run_pylinkjs_app(default_html='example.html')
```

**File: example.html**

_This HTML file provides the front-end structure, including the button that triggers the Python function and a link to example2.html._
```html
<head>
    <!-- jquery (requires for pyLinkJS) -->
    <script src="https://cdn.jsdelivr.net/npm/jquery@3.6.1/dist/jquery.min.js"></script>

    <!-- bootstrap (requires for pyLinkJS UI Helpers) -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.1/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.1/dist/js/bootstrap.bundle.min.js"></script>
</head>

<body>
  <a href='example2.html'>Click here to go to example 2 page</a>
  <br>

  <!-- Button triggers the Python function `button_clicked` with parameters 'param1' and 'param2' when clicked. -->
  <button onclick="call_py('button_clicked', 'param1', 'param2');">Click me</button>
  <div id='divout'>?</div>
</body>
```

**File: example2.html**

_This is a simple HTML file that serves as the target page for the link in example.html._
```html
This is the example 2 page
```

<br>
<br>
<br>

# Documentation

## Event Handlers


### popstate
```python
def popstate(jsc, state, target):
    """ called when the webpage is transitioned to using the back or forward buttons on the browser.
    
        For single page apps, the state should be used to change the state of the page to mimic a back
        or forward button page movement
        
        Args:
            state - state of the page to transition to, i.e. "show_login"
            target - target url the page is transitioning to, i.e. "https://www.myapp.com/"
    """
```

### ready
Called when a webpage establishes a new connection for the first time on load.
```python
def ready(jsc: PyLinkJSClient, origin: str, pathname: str, search: str, *args: tuple):
    """
    Parameters:
        jsc (PyLinkJSClient): Client object for interacting with webpage elements.
        origin (str): Origin portion of the calling URL, e.g., "http://www.test.com".
        pathname (str): Path portion of the calling URL, e.g., "/myapp.html".
        search (str): Query string of the calling URL, e.g., "?query=a".
        *args (tuple): Additional arguments passed from the client, if any.
    """

```

### reconnect
Called when a webpage reconnects to the backend server after a broken connection.

```python
def reconnect(javascript_context: PyLinkJSClient, origin: str, pathname: str, search: str, *args: tuple):
    """
    Parameters:
        javascript_context (PyLinkJSClient): Object for interacting with webpage elements dynamically.
        origin (str): Origin portion of the calling URL, e.g., "http://www.test.com".
        pathname (str): Path portion of the calling URL, e.g., "/myapp.html".
        search (str): Query string of the calling URL, e.g., "?query=a".
        *args (tuple): Additional arguments passed from the client, if any.
    """
```

## PyLinkJS

### get_all_jsclients
```python
def get_all_jsclients():
    """ return all JSClient instances known by this server
    
        Returns
            a list of JSClient instances
     """
```

This function is used to retrieve JSClient instances from the server application when not in a callback where the jsc is provided.

```python
for jsc in PyLinkJS.get_all_jsclients():
    jsc.eval_js_code('alert("Hello to All!")')
```


### get_broadcast_jsclients
```python
def get_broadcast_jsclients(pathname):
    """ return all JSClient instances known by this server filtered by the pathname
    
        pathname - the pathname to filter by, i.e. /
    
        Returns
            a list of JSClient instances with the correct pathname
    """
```

This function is used to retrieve JSClient instances from the server application when not in a callback where the jsc is provided.

```python
for jsc in PyLinkJS.get_broadcast_jsclients('\'):
    jsc.eval_js_code('alert("Hello to All!")')
```


### run_pylinkjs_app
```python
def run_pylinkjs_app(**kwargs):
    """
    Starts a PylinkJS app with configurable settings.

    Parameters:
    -----------
    port : int, optional
        Port number for the app (default: 8300).
    default_html : str, optional
        Main HTML file (default: "index.html").
    html_dir : str, optional
        Directory for HTML files (default: ".").
    login_html_page : str, optional
        Login page file (default: "login.html").
    cookie_secret : str, required
        Secret for cookie encryption; set a unique, random string.
    heartbeat_callback : callable, optional
        Function called periodically for heartbeats (default: None).
    heartbeat_interval : int, optional
        Time in seconds between heartbeats (default: None).
    login_handler : tornado.web.RequestHandler, optional
        Custom login handler (default: built-in).
    logout_handler : tornado.web.RequestHandler, optional
        Custom logout handler (default: built-in).
    extra_settings : dict, optional
        Extra settings for the Tornado app.
    
    Example:
    --------
    run_pylinkjs_app(port=8500, default_html="example.html", cookie_secret="random_string")
    """
```

## JSClient (Core Methods)

### \__getitem\__

HTML elements in the browser can be accessed by their ID using the jsc item accessor.  For example if there was an element such as `<div id=x>Hello</div>` in the html page, then it could be accessed in python using `jsc['x']`.

### browser_download
```python
def browser_download(self, filename, filedata, blocking=False):
    """ download a file from the backend to the users computer through the browser
    
        filename - the default name of the file to save as
        filedata - the binary data of the file to download
        blocking - if True, then this function will not return until the file has completed downloading
    """
```

This function will force a download of a file to the user's computer through the browser.

```python
# push a download of the file named test.txt containing the text "Hello World!" to the user's browser
jsc.browser_download('test.txt', "Hello World!")
```

### eval_js_code
```python
def eval_js_code(self, js_code, blocking=True):
    """ request that the browser evaluate javascript code
    
        js_code - the javascript code to execute
        blocking - if True, this function will not return until the javascript has completed execution
        
        Returns:
            the data that the executed javascript evaluates to
    """
```

Any arbitrary javacode can be run using this function

```python
# example call to show a messagebox from the browser
jsc.eval_js_code('alert("Hello");')

# the function will return whatever the javascript code evaluates to, in this case the function will return 6
jsc.eval_js_code('2 + 4')

# call an javascript function with parameters
jsc.eval_js_code('call_some_javascript_function(2, 3)')

# execute jquery code
jsc.eval_js_code('$("#myelement").html("Hello")')
```

### get_broadcast_jscs
```python
def get_broadcast_jscs(self):
    """ return all JSClient instances known by this server """                    
```

This is used to broadcast commands to all clients connected to this server.  For example, a chat program, this could be used to update the chat messages on all clients.

```python
for jsc in jsc.get_broadcast_jscs():
    jsc.eval_js_code('alert("Hello to All!")')
```

### get_pathname
```python
def get_pathname(self):
    """ return the path portion of the url of the browser bound to the JSClient instance
        
        For example, if the url of the JSClient is http://www.test.com/origin?query=a then this
        function would return /origin
    """
```

### tag
A property bag specific to each jsc which can store application information.  For example if 3 clients connected to the application, each would have it's own instance of a jsClient with their own prospective property bags to store application information.  This can be used to store state for each individual session on the server side.

```python
    jsc.tag['current_player_level'] = 5
    jsc.tag['current_player_stats'] = {'xp': 200, 'name': 'bob'}
```

## JSClient (Modal UI Methods)

### modal_alert
```python
def modal_alert(self, title, body, callback=''):
    """ Shows a modal alert dialog with an OK button

        Args:
            title - html title to show in the modal dialog
            body - html body to show in the modal dialog
            callback - callback in string form for when the OK buttion is clicked,
                       i.e. onclick="call_py('btn_clicked', 'create_new_item_save');"
    """
```
Example
```python
# show a messagebox with an OK button, if callback is specified, a python function can
# be called when the OK button is clicked
jsc.modal_alert('title html', 'body html)

# print the response
print(jsc.modal_input_get_text())
```

### modal_confirm
```python
def modal_confirm(self, title, body, callback=''):
    """ Shows a modal confirm dialog with OK and Cancel buttons

        Args:
            title - html title to show in the modal dialog
            body - html body to show in the confirm dialog
            callback - callback in string form for when the OK buttion is clicked,
                       i.e. onclick="call_py('btn_clicked', 'create_new_item_save');"
        """
```
Example
```python
# show a confirmation dialog with OK and cancel buttons, a python functon can
# be called when the OK button is clicked
jsc.modal_confirm('title html', 'body html',
                  """onclick="call_py('btn_clicked', 'create_new_item_save');" """)
```

### modal_input
```python
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
```
See modal_input_get_text function for example

### modal_input_get_text
```python
def modal_input_get_text(self):
    """ return the text from the last modal_input

        Returns:
            text from the input box of the last shown modal input
    """
```
Example
```python
# show an input modal allowing the user to enter in text
jsc.modal_input('title html', 'Type your answer in this box')

# print the response
print(jsc.modal_input_get_text())
```

### modal_new
```python
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
                            {'text': 'OK', 'classes': 'btn-primary', 'attributes': 'onclick="call_py("btn_clicked", "ok_btn")'}])
            modal_id - id of the modal to create
            autoshow - if True, this modal will be automatically shown, if False, an explicit call to modal_show is needed
                       to show this modal
    """
```
Example
```python
# create a new modal dialog which will automatically be shown to the user
# the python function btn_clicked will be called with parameter "ok_btn" when the OK button is clicked
jsc.modal_new('title html',
              'body html',
              [{'text': 'Cancel', 'classes': 'btn-secondary', 'attributes': 'data-bs-dismiss="modal"'},
               {'text': 'OK', 'classes': 'btn-primary', 'attributes': 'onclick="call_py("btn_clicked", "ok_btn")'}])
```

### modal_show
```python
def modal_show(self, modal_id='jsclient_modal'):
    """ show a modal created with the modal_new function

        Args:
            modal_id - id of the modal to show
    """
```
Example
```python
# create the modal dialog first with autoshow set to False
jsc.modal_new('title html',
              'body html',
              [{'text': 'Cancel', 'classes': 'btn-secondary', 'attributes': 'data-bs-dismiss="modal"'},
               {'text': 'OK', 'classes': 'btn-primary', 'attributes': 'onclick="call_py("btn_clicked", "ok_btn")'}],
               autoshow=False)

# modify the dialog classes, styles, etc. using eval_js_code

# show the dialog after modification
jsc.modal_show()
```

## JSClient (Select Element Methods)

### `select_get_options`

```python
def select_get_options(self, select_selector):
    """
    Retrieves value/text pairs for each option in a `<select>` element.

    Args:
        select_selector (str): jQuery selector for the `<select>` element.

    Returns:
        list: A list of `[value, text]` pairs for each option.
              Example: [['value_a', 'text_a'], ['value_b', 'text_b']]
    """
```
Example
```python
jsc.select_get_options('#myselect')
# returns [['a_val', 'a_text'], ['b_val', 'b_text']]
```

### `select_get_selected_options`

Retrieves the selected options from a `<select>` element.

```python
def select_get_selected_options(self, select_selector):
    """
    Args:
        select_selector (str): jQuery selector for the `<select>` element.

    Returns:
        list: A list of selected `[value, text]` pairs.
              Example: [['value_a', 'text_a'], ['value_b', 'text_b']]
    """
```
Example
```python
jsc.select_get_selected_options('#myselect')
# for a multiple select, returns [['a_val', 'a_text'], ['b_val', 'b_text']]
# for a single select, returns [['a_val', 'a_text']]
```

### select_set_options
```python
def select_set_options(self, select_selector, new_options):
    """
    Replaces all options in a `<select>` element with new options.

    Args:
        select_selector (str): jQuery selector for the target `<select>` element.
        new_options (list): List of options, each as:
            - `[value, text]` pair: sets `value` and display text separately.
            - Single string: sets both `value` and text to the same string.

    Example:
        select_set_options('#dropdown', [['v1', 'Option 1'], 'Option 2'])
    """
```
Example
```python
# will replace all options with two options
#   <option value='a_val'>a_text</option>
#   <option value='b_val'>b_text</option>
jsc.select_set_options('#myselect', [['a_val', 'a_text'], ['b_val', 'b_text']])

# will replace all options with two options
#   <option value='a'>a</option>
#   <option value='b'>b</option>
jsc.select_set_options('#myselect', ['a', 'b']])
```

### `select_set_selected_options`

Sets the selected options in a `<select>` element.

```python
def select_set_selected_options(self, select_selector, option_values):
    """
    Args:
        select_selector (str): jQuery selector for the `<select>` element.
        option_values (list or str): List of option values to select, or a single value to select.
    """
```
Example
```python
# to set multiple selected options
jsc.select_set_selected_options('#myselect', ['a_val', 'b_val'])

# to set a single selected option, first option with a single item list
jsc.select_set_selected_options('#myselect', ['a_val'])

# to set a single selected option, second option without the list
jsc.select_set_selected_options('#myselect', [a_val])
```

<br>
<br>
<br>

## PNG PDF Output
There is built in functionality to generate PNG and PDF output of a pyLinkJS website.  Simply add the output=png or output=pdf parameter to the url

Example
```http://mywebsite.com?output=png```
```http://mywebsite.com?output=pdf```

Additional parameters that can be passed are

- print_timeout: seconds to wait for webpage to finish loading, default is 10
- print_orientation: landscape or portrait, default is portrait (pdf only)
- print_force_scale: force a scaling factor (pdf only)
- print_force_fit: force the page width to fit on the page (pdf only)
- print_extra_delay: extra delay in seconds to allow the browser to render after loading has finished, default is 0

In the html javascript template some hints can be provided to the printing engine

```var HINT_PRINT_PAGE_READY = 0;```

```var HINT_PRINT_TIMEOUT = 30;```

The printing engine will wait until HINT_PRINT_PAGE_READY is set to a non-zero value before rendering the PNG or PDF.

The printing engine will use the HINT_PRINT_TIMEOUT as the timeout value if print_timeout was not explicitly passed in.

Example
```http://mywebsite.com?output=pdf&print_timeout=15&print_orientation=portrait&print_force_fit=1&print_extra_delay=5```

<br>
<br>
<br>

# Useful Code Examples

## Broadcast to all connected browsers
This example will update the html of the element with id of divout_broadcast on all connected browsers
```python
""" example of how to broadcast a change to all webpages """
t = time.time()
for bjsc in jsc.get_broadcast_jscs():
    bjsc['#divout_broadcast'].html = t
```

## Broadcast to all connected browsers on a separate thread
It is possible to broadcast commands to all connected web pages on a different thread by using the example code below.
This may be useful when polling in the main app and sending updates upon detection of a trigger

```python
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
```

# To use pyLinkJS behind an Apache Reverse Proxy subdirectory /foo
The application will run on port 9150 on localhost, apache will reverse proxy the application from http://localhost/foo
```python
ProxyPreserveHost On
ProxyRequests Off
ProxyPassMatch /foo/(websocket/0\..*) ws://127.0.0.1:9150/$1
ProxyPassReverse /foo/(websocket/0\..*) ws://127.0.0.1:9150/$1
ProxyPass /foo/ http://127.0.0.1:9150/
ProxyPassReverse /foo/ http://127.0.0.1:9150/
```






