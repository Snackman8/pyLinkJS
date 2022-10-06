# pyLinkJS
Simple bridge to allow Python to communicate with JavaScript

# Table of Contents

[Basic Example](#basic-example)

[Documentation](#documentation)
- [Event Handlers](#event-handlers)
- [PyLinkJS](#pylinkjs-1)
- [JSClient (Core Methods)](#jsclient-core-methods)
- [JSClient (Select Element Methods)](#jsclient-select-element-methods)

[Useful Code Examples](#useful-code-examples)

# Basic Example

Create the two files below for a simple example

### example.py
```python
import logging
import datetime
from pylinkjs.PyLinkJS import run_pylinkjs_app, Code

def button_clicked(jsc, a, b):
    """ simple example of a button click """
    jsc['#divout'].html = "Current Time: " + datetime.datetime.now().strftime('%H:%M:%S')
    jsc['#divout'].css.color = 'red'
    jsc['#divout'].click = Code('function() { alert("AA"); }')


# start the thread and the app
logging.basicConfig(level=logging.DEBUG, format='%(relativeCreated)6d %(threadName)s %(message)s')
run_pylinkjs_app(default_html='example.html')
```

### example.html
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
  <button onclick="call_py('button_clicked', 'param1', 'param2');">Click me</button>
  <div id='divout'>?</div>
</body>
```

### example2.html
```html
This is the example 2 page
```

---
# Documentation

## Event Handlers

### ready
```python
def ready(jsc, origin, pathname, search, *args)
    """ called when a webpage creates a new connection the first time on load """
    print('Ready', origin, pathname, search, args)
```
&nbsp;&nbsp;&nbsp;&nbsp;This callback is triggered when a page is loaded and ready.  If the url called was http://www.test.com/myapp.html?query=a

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**origin** - contains the origin portion of the calling URL, i.e. "http://www.test.com"

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**pathname** - contains the path portion of the calling URL, i.e. "/myapp.html"

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**search** - contains the search portion of the calling URL, i.e. "?query=a"


### reconnect
```python
def reconnect(jsc, origin, pathname, search, *args)
    """ called when a webpage automatically reconnects a broken connection """
    print('Reconnect', origin, pathname, search, args)
```
&nbsp;&nbsp;&nbsp;&nbsp;This callback is triggered when an existing page reconnects to the backend server from a broken websocket connection.  If the url called was http://www.test.com/myapp.html?query=a

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**origin** - contains the origin portion of the calling URL, i.e. "http://www.test.com"

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**pathname** - contains the path portion of the calling URL, i.e. "/myapp.html"

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**search** - contains the search portion of the calling URL, i.e. "?query=a"

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
    """ this function runs a pylinkjs application
    
        port - port number to run application on, default is 8300
        default_html - filename for the default html file, defaults to index.html
        html_dir - directory containing html files, defaults to .
        login_html_page - filename for the default login html page, defaults to prepackaged login.html
        cookie_secret - secret cookie string, please set this to a random string
        heartbeat_callback - heartbeat function name which will be called periodically, defaults to None
        heartbeat_interval - interval in seconds when the heartbeat_callback function will be called, defaults to None
        login_handler - tornado handler for login, defaults to built in Login Handler
        logout_handler - tornado handler for login, defaults to built in Logout Handler
        extra_settings - dictionary of extra settings that will be made available to the tornado application
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
    jsc['current_player_level'] = 5
    jsc['current_player_stats'] = {'xp': 200, 'name': 'bob'}
```


## JSClient (Select Element Methods)

### select_get_options
```python
def select_get_options(self, select_selector):
    """ retrieve the value / text pair of each option in the selector

        Args:
            select_selector - jquery selector for the select element

        Returns:
            list of options.  each option is a two element list, first element is the value, second element is the text
            i.e. [['value_a', 'text_a'], ['value_b', 'text_b']]
    """
```
Example
```python
jsc.select_get_options('#myselect')
# returns [['a_val', 'a_text'], ['b_val', 'b_text']]
```

### select_get_selected_options
```python
    def select_get_selected_options(self, select_selector):
        """ retrieve the selected options

            Args:
                select_selector - jquery selector for the select element

            Returns:
                list of selected options.  each option is a two element list,
                first element is the value, second element is the text
                i.e. [['value_a', 'text_a'], ['value_b', 'text_b']]
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
        """ replaces all the options in the select with new options

            Args:
                select_selector - jquery selector for the select element
                new_options - list of new options,
                              each option is a two element list of value and text,
                              i.e. [['value_a', 'text_a'], ['value_b', 'text_b']]
        """
```
Example
```python
# will replace all options with two options
#   <option value='a_val'>a_text</option>
#   <option value='b_val'>b_text</option>
jsc.select_set_options('#myselect', [['a_val', 'a_text'], ['b_val', 'b_text']])
```

### select_set_selected_options
```python
    def select_set_selected_options(self, select_selector, option_values):
        """ selectes options in the select

            Args:
                select_selector - jquery selector for the select element
                option_values - list of options values to select to a single value to select
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







