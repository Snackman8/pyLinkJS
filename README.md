# pyLinkJS
Simple bridge to allow Python to communicate with JavaScript

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
  <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
</head>

<body>
  <button onclick="call_py('button_clicked', 'param1', 'param2');">Click me</button>
  <div id='divout'>?</div>
</body>
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
&nbsp;&nbsp;&nbsp;&nbsp;This callback is triggered when a page is loaded and ready.  If the url called was http://www.test.com/origin?query=a

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**origin** - contains the origin portion of the calling URL, i.e. "http://www.test.com"

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**pathname** - contains the path portion of the calling URL, i.e. "/"

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**search** - contains the search portion of the calling URL, i.e. "?query=a"


### reconnect
```python
def reconnect(jsc, origin, pathname, search, *args)
    """ called when a webpage automatically reconnects a broken connection """
    print('Reconnect', origin, pathname, search, args)
```
&nbsp;&nbsp;&nbsp;&nbsp;This callback is triggered when an existing page reconnects to the backend server from a broken websocket connection.  If the url called was http://www.test.com/origin?query=a

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**origin** - contains the origin portion of the calling URL, i.e. "http://www.test.com"

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**pathname** - contains the path portion of the calling URL, i.e. "/"

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

## JSClient (JSC)

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

### select_add_option
```python
    def select_add_option(self, select_selector, value, text):
        """ add an option to an HTML select element
        
            select_selector - jquery selector for the select element
            value - value of the option to add
            text - text of the option to add
        """
```
In the example below, there is an html element like below

```html
<select id=myselect>
    <option value="a">aa</option>
    <option value="b">bb</option>
</select>
```

to add a new optioon to the end of the select
```python
jsc.select_add_option('#myselect', 'c', 'cc')
```

The resulting html will be
```html
<select id=myselect>
    <option value="a">aa</option>
    <option value="b">bb</option>
    <option value="c">cc</option>
</select>
```

### select_get_selected_option
```python
def select_get_selected_option(self, select_selector):
    """ get the active option of an HTML select element
       
        select_selector - jquery selector for the select element
            
        Returns:
            the value of the active option
    """
```
In the example below, there is an html element like below

```html
<select id=myselect>
    <option value="a">aa</option>
    <option value="b">bb</option>
</select>
```

to retrieve the current active option, use the code below
```python
jsc.select_get_selected_option('#myselect')
```

### select_set_selected_option
```python
def select_set_selected_option(self, select_selector, option_value):
    """ select an option inside a HTML select element
    
        select_selector - jquery selector for the select element
        option_value - value of the option to select
    """
```

In the example below, there is an html element like below

```html
<select id=myselect>
    <option value="a">aa</option>
    <option value="b">bb</option>
</select>
```

to force the select to have the "b" option, active we would use the code below

```python
jsc.select_set_selected_option('#myselect', 'b')
```

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







