# pyLinkJS
A simple bridge to allow Python to communicate with JavaScript.

---

### Table of Contents

- **[Installation](#installation)**
- **[Skeleton Example](#skeleton-application-example)**
- **[Basic Example](#basic-example)**
- **[Documentation](#documentation)**
  - [Event Handlers](#event-handlers)
  - [PyLinkJS](#pylinkjs-1)
  - [PyLinkJSClient (Core Methods)](#PyLinkJSClient-core-methods)
  - [PyLinkJSClient (Modal UI Methods)](#PyLinkJSClient-modal-ui-methods)
  - [PyLinkJSClient (Select Element Methods)](#PyLinkJSClient-select-element-methods)
  - [PNG/PDF Output](#png-pdf-output)
- **[Useful Code Examples](#useful-code-examples)**
- **[Using pyLinkJS Behind an Apache Reverse Proxy](#using-pylinkjs-behind-an-apache-reverse-proxy)**
- **[Important Hints for ChatGPT to Generate Correct Code](##to-use-pylinkjs-behind-an-apache-reverse-proxy-subdirectory-foo)**


---

## Installation

To install `pyLinkJS`, you have two options:

1. **Install directly from the Git repository using `pip`:**

   ```bash
   pip3 install git+https://github.com/Snackman8/pyLinkJS
   ```

2. **Clone the repository and install using `pip`:**

   ```bash
   cd ~
   git clone https://github.com/Snackman8/pyLinkJS
   cd pyLinkJS
   sudo pip3 install .
   ```
   
---

## Skeleton Application Example

This minimal structure serves as a starting point for building a PylinkJS application—a "Hello World" app.

- By convention, the HTML and Python files share the same name, though this is not required.
- This skeleton example consists of two files: `skeleton.py` and `skeleton.html`.
- Runs on port 8300.
- The application is fully functional and requires no additional code to run.

**File: skeleton.py**

```python
import logging
import datetime
from pylinkjs.PyLinkJS import run_pylinkjs_app

def button_clicked(jsc):
    """
    Handles button click events, updating the webpage's HTML and styles.

    Parameters:
        jsc : A communication channel automatically injected by the framework into the webpage, allowing Python to interact with and modify JavaScript-controlled page elements in real-time.
    """
    # Sets the inner HTML of #divout to display the current time
    jsc['#divout'].html = "Current Time: " + datetime.datetime.now().strftime('%H:%M:%S')
    # Changes the text color of #divout to red
    jsc['#divout'].css.color = 'red'

# Starts the PylinkJS app serving `example.html` on `localhost:8300` (default port) for browser-Python interaction.
logging.basicConfig(level=logging.DEBUG, format='%(relativeCreated)6d %(threadName)s %(message)s')
run_pylinkjs_app(default_html='skeleton.html', port=8300)
```

**File: skeleton.html**

_This HTML file provides the front-end structure, including the button that triggers the Python function._

```html
<html>
<!-- Note: jQuery and Bootstrap are automatically injected by the framework. -->
<!-- Note: HTML comment-based template systems like Tornado are not compatible with PylinkJS.
           Avoid using templating syntax within HTML comments to ensure compatibility. -->
<!-- Note: the call_py JavaScript function is used to call Python functions in the Python source code. -->

<body>
  <!-- Note: The PyLinkJS JavaScript function `call_py` is used to call Python functions from JavaScript. -->
  <button onclick="call_py('button_clicked');">Click me</button>
  <div id='divout'>?</div>
</body>
</html>
```

---

## Basic Example

This example demonstrates a simple PylinkJS application with interactive Python-JavaScript functionality. Unlike the **Skeleton Application Example**, this example shows how to modify JavaScript event handlers from Python using the `Code` object and demonstrates passing parameters from JavaScript to Python by including dummy parameters in the function call.

- The application consists of three files: `basic_example.py`, `basic_example.html`, and `basic_example2.html`.
- The HTML and Python files share the same name by convention, though this is not required.
- Runs on port 8300.
- This application is fully functional and requires no additional code to run.

**File: basic_example.py**

```python
import logging
import datetime
from pylinkjs.PyLinkJS import run_pylinkjs_app, Code

def button_clicked(jsc, a, b):
    """
    Handles button click events, updating the webpage's HTML and styles.

    Parameters:
        jsc : A communication channel automatically injected by the framework into the webpage, allowing Python to interact with and modify JavaScript-controlled page elements in real-time.
        a : A dummy parameter to demonstrate passing data from JavaScript to Python.
        b : A dummy parameter to demonstrate passing data from JavaScript to Python.

    JavaScript Example:
        call_py('button_clicked', 'param1', 'param2');
    """
    # Sets the inner HTML of #divout to display the current time
    jsc['#divout'].html = "Current Time: " + datetime.datetime.now().strftime('%H:%M:%S')
    # Changes the text color of #divout to red
    jsc['#divout'].css.color = 'red'
    # Adds a click event to #divout that shows an alert with the message "AA" when clicked
    jsc['#divout'].click = Code('function() { alert("AA"); }')
    # use eval_js_code to run arbitrary javascript code to change the output
    jsc.eval_js_code(f"""$('#divout2').html('{datetime.datetime.now().strftime('%H:%M:%S')}');""")

# Starts the PylinkJS app serving `basic_example.html` on `localhost:8300` for browser-Python interaction.
logging.basicConfig(level=logging.DEBUG, format='%(relativeCreated)6d %(threadName)s %(message)s')
run_pylinkjs_app(default_html='basic_example.html', port=8300)
```

**File: basic_example.html**

_This HTML file provides the front-end structure, including the button that triggers the Python function and a link to `basic_example2.html`._

```html
<html>
<!-- Note: jQuery and Bootstrap are automatically injected by the framework. -->
<!-- Note: HTML comment-based template systems like Tornado are not compatible with PylinkJS.
           Avoid using templating syntax within HTML comments to ensure compatibility. -->
<!-- Note: The `call_py` JavaScript function is used to call Python functions in the Python source code. -->

<body>
  <a href='basic_example2.html'>Click here to go to example 2 page</a>
  <br>
  
  <!-- Button triggers the Python function `button_clicked` with parameters 'param1' and 'param2' when clicked.
       These parameters are passed to the Python function to demonstrate data transfer from JavaScript to Python. -->
  <button onclick="call_py('button_clicked', 'param1', 'param2');">Click me</button>
  
  <!-- The `divout` element will be updated by Python code to show the current time and
       will also have a new click handler attached that triggers an alert when clicked. -->
  <div id='divout'>?</div>

  <!-- The `divout2` element will be updated by the Python code using the `eval_js_code` function,
       which can execute arbitrary JavaScript code. -->
  <div id='divout2'></div>
</body>
</html>
```

**File: basic_example2.html**

_This is a simple HTML file that serves as the target page for the link in `basic_example.html`._

```html
<html>
  <body>
    <p>This is the example 2 page.</p>
  </body>
</html>
```

---

# Documentation

## Event Handlers

### popstate
```python
def popstate(jsc, state, target):
    """
    Event handler called when the webpage is transitioned to using the back or forward buttons on the browser.
    
    For single page apps, the state should be used to change the state of the page to mimic a back
    or forward button page movement

    Parameters:
        state (str): state of the page to transition to, i.e. "show_login"
        target (str): target url the page is transitioning to, i.e. "https://www.myapp.com/"
    """
```

### ready

```python
def ready(jsc: PyLinkJSClient, origin: str, pathname: str, search: str, *args: tuple):
    """
    Event handler Called when a webpage establishes a new connection for the first time on load.

    Parameters:
        jsc (PyLinkJSClient): Client object for interacting with webpage elements.
        origin (str): Origin portion of the calling URL, e.g., "http://www.test.com".
        pathname (str): Path portion of the calling URL, e.g., "/myapp.html".
        search (str): Query string of the calling URL, e.g., "?query=a".
        *args (tuple): Additional arguments passed from the client, if any.
    """

```

### reconnect
```python
def reconnect(javascript_context: PyLinkJSClient, origin: str, pathname: str, search: str, *args: tuple):
    """
    Event handler called when a webpage reconnects to the backend server after a broken connection.

    Parameters:
        javascript_context (PyLinkJSClient): Object for interacting with webpage elements dynamically.
        origin (str): Origin portion of the calling URL, e.g., "http://www.test.com".
        pathname (str): Path portion of the calling URL, e.g., "/myapp.html".
        search (str): Query string of the calling URL, e.g., "?query=a".
        *args (tuple): Additional arguments passed from the client, if any.
    """
```

## PyLinkJS

### `get_all_jsclients`
```python
def get_all_jsclients() -> list[PyLinkJSClient]:
    """
    Retrieves all JSClient instances from the server application when not in a callback where a jsc instance is provided.

    Returns:
        list[PyLinkJSClient]: A list of all `JSClient` instances managed by the server.
    """
```

This function is used to retrieve JSClient instances from the server application when not in a callback where the jsc is provided.

**Example**
```python
# Loop through all JSClient instances connected to the server
for jsc in PyLinkJS.get_all_jsclients():
    # Execute JavaScript code in each connected client's browser
    # In this example, it triggers an alert with the message "Hello to All!"
    jsc.eval_js_code('alert("Hello to All!")')
```

### get_broadcast_jsclients
```python
def get_broadcast_jsclients(pathname: str) -> list[PyLinkJSClient]:
    """
    Retrieves all PyLinkJSClient instances from the server application filtered by the specified pathname.
    Useful when not in a callback where a `jsc` instance is provided.

    Args:
        pathname (str): The pathname to filter by, e.g., "/".

    Returns:
        list[PyLinkJSClient]: A list of `PyLinkJSClient` instances with the specified pathname.
    """
```

This function is used to retrieve JSClient instances from the server application when not in a callback where the jsc is provided.

```python
# Loop through all PyLinkJSClient instances connected with the specified pathname
for jsc in PyLinkJS.get_broadcast_jsclients('/'):
    # Execute JavaScript code in each matching client's browser
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

## PyLinkJSClient (Core Methods)

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
        the javascript code is executed in the global javascript context so it remembers which variables have been previously declared
    
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

## PyLinkJSClient (Modal UI Methods)

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

## PyLinkJSClient (Select Element Methods)

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

# Important Hints for ChatGPT to Generate Correct Code
- Tornado Template is not allowed in the HTML file
- use the ready event handler for code that should be run when the page is loaded, do not use call_py inside the onload, it won't work
- use the run_pylinkjs_app function to start the web service






