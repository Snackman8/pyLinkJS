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

## JSClient (JSC)

### \__getitem\__

HTML elements in the browser can be accessed by their ID using the jsc item accessor.  For example if there was an element such as `<div id=x>Hello</div>` in the html page, then it could be accessed in python using `jsc['x']`.

### browser_download

### eval_js_code

### get_broadcast_jscs

### get_pathname

### select_add_option

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







