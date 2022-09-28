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







