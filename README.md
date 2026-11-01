# pyLinkJS
Call Python from browser JavaScript and update the page from Python.

---

### Table of Contents

- **[Installation](#installation)**
- **[Skeleton Example](#skeleton-application-example)**
- **[Basic Example](#basic-example)**
- **[Development to Deployment](#development-to-deployment)**
- **[Security Controls](#security-controls)**
- **[How to Use with Codex in VS Code](#how-to-use-with-codex-in-vs-code)**
- **[Documentation](#documentation)**
  - [Event Handlers](#event-handlers)
  - [PyLinkJS](#pylinkjs)
  - [Controlling which files can be served](#controlling-which-files-can-be-served)
  - [High-security callback mode](#high-security-callback-mode)
  - [PyLinkJSClient (Core Methods)](#pylinkjsclient-core-methods)
  - [PyLinkJSClient (Modal UI Methods)](#pylinkjsclient-modal-ui-methods)
  - [PyLinkJSClient (Select Element Methods)](#pylinkjsclient-select-element-methods)
  - [PNG/PDF Output](#png-pdf-output)
- **[Useful Code Examples](#useful-code-examples)**
- **[Using pyLinkJS Behind an Apache Reverse Proxy](#using-pylinkjs-behind-an-apache-reverse-proxy)**
- **[LLM Reference (Code Generation Contract)](#llm-reference-code-generation-contract)**

---

## Installation

Install `pyLinkJS` in a virtual environment. On Ubuntu:

```bash
# install dependencies on Ubuntu
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv

# create a virtual environment in the venv directory
python3 -m venv venv

# activate the virtual environment
source venv/bin/activate

# install the pyLinkJS package directly from GitHub
pip install git+https://github.com/Snackman8/pyLinkJS

# (Optional) Clone the repository to access example code (see the examples/ directory)
git clone https://github.com/Snackman8/pyLinkJS

# (Optional) Enable printing support in PyLinkJS apps.
# Install Playwright's Chromium browser so PNG and PDF output can be generated.
# The command may ask you to install system dependencies.
# If it suggests "sudo playwright install-deps", run this instead to use the venv's binary:
#     sudo $(which playwright) install-deps
playwright install chromium

# (Optional) Run the Hello World example.
# This starts a server on port 8300 — open http://localhost:8300 in your browser to see it.
# If accessing from another machine, replace "localhost" with the IP of the server running pyLinkJS.
# If running on a locked-down server, you may need to open port 8300 in the firewall to allow access.
# Press Ctrl+C in the terminal to stop the server.
python3 pyLinkJS/examples/hello_world/hello_world.py
```

## Skeleton Application Example

A button calls Python, which updates the page. Save `skeleton.py` and
`skeleton.html` in the same directory, then run `python3 skeleton.py` and open
`http://localhost:8300/`.

This example uses automatic callback lookup for rapid development. Before
release, [switch to high-security mode](#switching-to-high-security-mode).

**File: skeleton.py**

```python
import argparse
import logging
import datetime
from pylinkjs.PyLinkJS import run_pylinkjs_app

def button_clicked(jsc):
    """Show the time in red.

    Parameters:
        jsc: The client object supplied by pyLinkJS for the page that called
             this function. Use it to read or update page elements.
    """
    # Set the inner HTML of the element with id="divout" to the current time.
    jsc['#divout'].html = "Current Time: " + datetime.datetime.now().strftime('%H:%M:%S')
    # Change that element's CSS text color to red.
    jsc['#divout'].css.color = 'red'

# Accept an optional --port argument; use port 8300 if it is omitted.
parser = argparse.ArgumentParser()
parser.add_argument('--port', type=int, required=False, default=8300)
args = parser.parse_args()

# Open http://localhost:8300 in your browser.
logging.basicConfig(level=logging.DEBUG, format='%(relativeCreated)6d %(threadName)s %(message)s')
# Serve skeleton.html from the current directory and handle its Python callbacks.
run_pylinkjs_app(default_html='skeleton.html', port=args.port)
```

**File: skeleton.html**

```html
<html>
<!-- pyLinkJS injects jQuery and Bootstrap. -->

<body>
  <!-- call_py sends the function name to Python; pyLinkJS supplies its jsc argument. -->
  <button onclick="call_py('button_clicked');">Click me</button>
  <!-- Python updates this element through jsc['#divout']. -->
  <div id='divout'>?</div>
</body>
</html>
```

---

## Basic Example

Pass arguments with `call_py`, assign a JavaScript event handler with `Code`,
and run JavaScript with `eval_js_code`.

It uses the same development setup as the skeleton example.

Save these three files in the same directory. Run `python3 basic_example.py`
and open `http://localhost:8300/`.

**File: basic_example.py**

```python
import argparse
import logging
import datetime
from pylinkjs.PyLinkJS import run_pylinkjs_app, Code

def button_clicked(jsc, a, b):
    """Handle a button click and update the page's HTML and styles.

    Parameters:
        jsc: The client object supplied by pyLinkJS for the page that called
             this function. Use it to read or update page elements.
        a: The first argument passed from JavaScript ('param1' below).
        b: The second argument passed from JavaScript ('param2' below).

    JavaScript example:
        call_py('button_clicked', 'param1', 'param2');

    JavaScript supplies a and b; pyLinkJS supplies jsc as the first parameter.
    This example accepts a and b to demonstrate argument passing; it does not
    otherwise use them.
    """
    # Set the inner HTML of the element with id="divout" to the current time.
    jsc['#divout'].html = "Current Time: " + datetime.datetime.now().strftime('%H:%M:%S')
    # Change that element's CSS text color to red.
    jsc['#divout'].css.color = 'red'
    # Add a JavaScript click handler to #divout that shows an alert saying "AA".
    # Code(...) sends a JavaScript function, rather than treating it as a string.
    jsc['#divout'].click = Code('function() { alert("AA"); }')
    # Run JavaScript in the browser to update a second element, #divout2.
    jsc.eval_js_code(f"""$("#divout2").html("{datetime.datetime.now().strftime('%H:%M:%S')}");""")

# Accept an optional --port argument; use port 8300 if it is omitted.
parser = argparse.ArgumentParser()
parser.add_argument('--port', type=int, required=False, default=8300)
args = parser.parse_args()

# Open http://localhost:8300 in your browser.
logging.basicConfig(level=logging.DEBUG, format='%(relativeCreated)6d %(threadName)s %(message)s')
# Serve basic_example.html from the current directory with automatic callback lookup.
run_pylinkjs_app(default_html='basic_example.html', port=args.port)
```

**File: basic_example.html**

```html
<html>
<!-- pyLinkJS injects jQuery and Bootstrap. -->

<body>
  <!-- Follow a normal HTML link to another page served by the app. -->
  <a href='basic_example2.html'>Click here to go to example 2 page</a>
  <br/>
  
  <!-- Pass 'param1' and 'param2' as a and b to button_clicked(jsc, a, b). -->
  <button onclick="call_py('button_clicked', 'param1', 'param2');">Click me</button>
  
  <!-- Python updates this element and gives it a JavaScript click handler. -->
  <div id='divout'>?</div>

  <!-- Python updates this element by running JavaScript with eval_js_code. -->
  <div id='divout2'></div>
</body>
</html>
```

**File: basic_example2.html**

```html
<html>
  <body>
    <p>This is the example 2 page.</p>
  </body>
</html>
```

---

## Development to Deployment

Develop with automatic callback lookup, the default (`high_security=False`).
When the app is finished, enable high-security mode and register the callbacks
before release or access by untrusted users. The file allowlist stays active
in both modes.

```text
my_app/
├── mini_app.py
└── mini_app.html
```

**File: mini_app.py**

```python
import argparse
import datetime
import logging

from pylinkjs.PyLinkJS import run_pylinkjs_app


def ready(jsc, origin, pathname, search, *args):
    # pyLinkJS calls ready when the page first connects to the server.
    # .text sets an element's text content; '#status' selects id="status".
    jsc["#status"].text = "Connected"
    jsc["#divout"].text = "Click the button to update the time."


def reconnect(jsc, origin, pathname, search, *args):
    # Restore the page's initial state after reconnecting.
    ready(jsc, origin, pathname, search, *args)


def button_clicked(jsc):
    # Replace the output text when the HTML button calls this function.
    jsc["#divout"].text = datetime.datetime.now().strftime("Current Time: %H:%M:%S")


def main():
    # Let the app run on a different port with --port.
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8300)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    print(f"Open http://localhost:{args.port} in your browser.")
    # During development, pyLinkJS finds the callbacks automatically.
    run_pylinkjs_app(default_html="mini_app.html", port=args.port)


if __name__ == "__main__":
    main()
```

**File: mini_app.html**

```html
<html>
  <body>
    <!-- ready updates the connection status when the page connects. -->
    <p id="status"></p>
    <!-- call_py invokes button_clicked in Python, with jsc supplied by pyLinkJS. -->
    <button onclick="call_py('button_clicked');">Click me</button>
    <!-- Python writes the current time into this element. -->
    <div id="divout">?</div>
  </body>
</html>
```

From the app directory, run `python3 mini_app.py` and open
`http://localhost:8300/`.

### Switching to high-security mode

When the app is finished, replace the startup call in `main()` with:

```python
# Map callback names used by the browser to the Python functions it may call.
page_callbacks = {
    "ready": ready,
    "reconnect": reconnect,
    "button_clicked": button_clicked,
}
run_pylinkjs_app(
    default_html="mini_app.html",
    port=args.port,
    # Disable automatic lookup; allow only callbacks in the registry below.
    high_security=True,
    # These two URLs serve the same HTML file, so give them the same callbacks.
    callback_registry={"/": page_callbacks, "/mini_app.html": page_callbacks},
)
```

The callbacks and HTML stay the same. Register every callback each page uses,
including `ready` and `reconnect`. Only registered callbacks can then be invoked.

For deployment, we also recommend moving browser assets into `public/` and
setting `html_dir="public"`; Python files can stay outside it. See the
[backend layout](#high-security-callback-mode) for larger apps. Add
[authentication](#require-authentication-for-all-pages) if the app needs login.
High-security callback mode alone does not require authentication or a cookie
secret, and anyone who can reach the app can invoke its registered callbacks.

## Security Controls

| Control | What it controls |
| --- | --- |
| `html_dir` | The directory from which built-in file serving reads files. |
| `servable_file_regex` | Which files inside that directory may be downloaded. |
| `high_security=True` + `callback_registry` | Which Python callbacks browsers may invoke on each page. |
| `require_auth=True` + authentication setup | Whether built-in pages and WebSocket connections require login. |

Registered callbacks must still validate their arguments and check permissions
for the requested operation. Custom HTTP handlers must enforce their own access
controls. High-security callback mode can be used for public or authenticated apps.

## How to Use with Codex in VS Code

To create an app with Codex:

1. Open an empty folder in VS Code.
2. Open Codex in VS Code.
3. Paste the prompt below.

```text
First, download this project's README from GitHub into this empty folder as `pyLinkJS_readme.md`:
- URL: https://raw.githubusercontent.com/Snackman8/pyLinkJS/master/README.md
- Prefer: `curl -fL "https://raw.githubusercontent.com/Snackman8/pyLinkJS/master/README.md" -o pyLinkJS_readme.md`
- Fallback: `wget -O pyLinkJS_readme.md "https://raw.githubusercontent.com/Snackman8/pyLinkJS/master/README.md"`

Read `pyLinkJS_readme.md` and follow its "Development to Deployment" example
and "LLM Reference (Code Generation Contract)".

Starting from this empty folder:
1) Create a Python virtual environment named .venv if it does not already exist.
2) Activate/use .venv and install prerequisites needed for pyLinkJS demos.
3) Create `mini_app.py` and `mini_app.html` in the same directory using the development example.
4) Include required pyLinkJS event handlers (`ready`, `reconnect`) and one `call_py(...)` action handler.
5) Use `run_pylinkjs_app(default_html='mini_app.html', port=8300)` for rapid development.
   When asked to prepare the app for release, enable high_security=True and register
   its callbacks. Recommend a public directory for browser assets at that stage.
6) Keep the code simple and well-commented.
7) When the app starts, print the exact browser URL to open, e.g. `Open http://localhost:8300 in your browser.`
8) At the end, print exact run commands.

Do not ask me follow-up questions unless something is truly blocking.
```

# Documentation

## Event Handlers

### popstate
```python
def popstate(jsc, state, target):
    """
    Handle browser back/forward navigation. In a single-page app, restore the
    page state from the supplied history entry.

    Parameters:
        state (str): state of the page to transition to, i.e. "show_login"
        target (str): target url the page is transitioning to, i.e. "https://www.myapp.com/"
    """
```

### ready

```python
def ready(jsc: PyLinkJSClient, origin: str, pathname: str, search: str, *args: tuple):
    """
    Called when the page first connects to the server.

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
    Called when the page reconnects after losing its connection.

    Parameters:
        javascript_context (PyLinkJSClient): Client object for updating the page.
        origin (str): Origin portion of the calling URL, e.g., "http://www.test.com".
        pathname (str): Path portion of the calling URL, e.g., "/myapp.html".
        search (str): Query string of the calling URL, e.g., "?query=a".
        *args (tuple): Additional arguments passed from the client, if any.
    """
```

### on_404
```python
def on_404(path, uri, host, extra_settings, headers=None, body=b"", method="GET", *args):
    """
    Called for GET requests with no existing file and for POST requests handled
    by the built-in handler. Use this to implement ad hoc REST endpoints.
    Existing files rejected by servable_file_regex do not invoke this handler.

    Args:
        path: str  # path without leading slash, e.g. "run"
        uri: str   # full URI with query string
        host: str  # Host header
        extra_settings: dict  # app-defined settings
        headers: dict  # request headers (flattened)
        body: bytes  # raw request body (may be empty)
        method: str  # "GET", "POST", etc.
    Returns:
        tuple: (bytes response_body, str content_type, int status_code, dict headers_out?)
               headers_out is optional
    """
```

## PyLinkJS

### `get_all_jsclients`
```python
def get_all_jsclients() -> list[PyLinkJSClient]:
    """
    Return all connected clients. Useful outside callbacks, where no jsc is supplied.

    Returns:
        list[PyLinkJSClient]: A list of all `JSClient` instances managed by the server.
    """
```

**Example**
```python
# Send the JavaScript alert to every connected client.
for jsc in PyLinkJS.get_all_jsclients():
    jsc.eval_js_code('alert("Hello to All!")')
```

### get_broadcast_jsclients
```python
def get_broadcast_jsclients(pathname: str) -> list[PyLinkJSClient]:
    """
    Return connected clients on the given page URL path.

    Args:
        pathname (str): The pathname to filter by, e.g., "/".

    Returns:
        list[PyLinkJSClient]: A list of `PyLinkJSClient` instances with the specified pathname.
    """
```

```python
# Send the alert only to clients whose page URL path is '/'.
for jsc in PyLinkJS.get_broadcast_jsclients('/'):
    jsc.eval_js_code('alert("Hello to All!")')
```

### run_pylinkjs_app
```python
def run_pylinkjs_app(**kwargs):
    """
    Start a pyLinkJS application.

    Parameters:
    -----------
    port : int, optional
        Port number for the app (default: 8300).
    default_html : str, optional
        Main HTML file (default: "index.html").
    html_dir : str, optional
        Root directory for built-in file serving (default: ".").
    servable_file_regex : str, optional
        Fullmatch allowlist for file paths relative to html_dir. Defaults to case-insensitive
        HTML, CSS, JavaScript, common images and fonts. Overrides replace the default.
    high_security : bool, optional
        Restrict browser calls to callback_registry (default: False for rapid development).
        Enable before release.
    callback_registry : dict, optional
        Maps exact page URL paths to {callback_name: callable}; required when high_security=True.
        Use PyLinkJSCallback(func, allow_new_thread=True) to permit background execution.
    max_background_callbacks : int, optional
        Maximum concurrent background callbacks in high-security mode (default: 4).
    plugins : list, optional
        Plugin instances, such as an authentication plugin (default: []).
    login_html_page : str, optional
        Login page path used by a login handler. Authentication plugins configure their own page.
    cookie_secret : str, optional (required when using authentication)
        Secret for signing cookies, not encrypting them. Use a long random value.
    cookie_secure : bool, optional
        If True, authentication cookies are sent only over HTTPS (default: False for local HTTP development).
    cookie_httponly : bool, optional
        Prevents JavaScript from reading authentication cookies (default: True).
    cookie_samesite : {'Lax', 'Strict', 'None', None}, optional
        SameSite policy for authentication cookies (default: 'Lax').
    require_auth : bool, optional
        If True, unauthenticated HTTP requests are redirected to /login and unauthenticated
        websocket connections are rejected (default: False).
    heartbeat_callback : callable, optional
        Function called periodically for heartbeats (default: None).
    heartbeat_interval : int, optional
        Time in seconds between heartbeats (default: None).
    login_handler : tornado.web.RequestHandler, optional
        Custom login handler. Configure an authentication plugin or implement a login handler.
    logout_handler : tornado.web.RequestHandler, optional
        Custom logout handler (default: built-in).
    route_handlers : list, optional
        Additional Tornado handler tuples, for example
        [(r"/admin/users", AdminUsersHandler), (r"/api/users", UsersHandler, {"db_path": "users.sqlite3"})].
        This is useful for plugins that need to expose their own HTTP pages or APIs.
    extra_settings : dict, optional
        Extra settings for the Tornado app.
    on_404: callable, optional
        If provided, is called for GET and POST misses.
        Recommended signature: on_404(path, uri, host, extra_settings, headers, body, method, *args).
    
    Example:
    --------
    See Development to Deployment for a runnable app and its high-security configuration.
    """
```

### Controlling which files can be served

The default allowlist covers common browser assets; most apps need no regex
override. Point `html_dir` at `public/` to keep Python code and other private
files outside built-in file serving.

`html_dir` sets the directory from which files are served (default: `"."`).
`servable_file_regex` adds an allowlist: an existing file is served only if its
path relative to `html_dir` fully matches the regex. Paths use `/` separators,
without a leading slash, for example `images/logo.png`. Directory requests such
as `/` or `/reports/` are checked after resolving `default_html`.

The default is:

```python
r"(?i).*\.(?:html?|css|m?js|png|jpe?g|gif|svg|webp|avif|ico|bmp|woff2?|ttf|otf|eot)"
```

This allows `.html`, `.htm`, `.css`, `.js`, `.mjs`, `.png`, `.jpg`, `.jpeg`,
`.gif`, `.svg`, `.webp`, `.avif`, `.ico`, `.bmp`, `.woff`, `.woff2`, `.ttf`,
`.otf`, and `.eot`. The `(?i)` makes matching case-insensitive, so `.HTML`
and `.PNG` also work. A custom regex controls its own case sensitivity; omit
`(?i)` for case-sensitive matching. Invalid regexes fail at startup.

Other file types, including `.py`, `.txt`, `.md`, `.json`, configuration files,
databases, logs, and backups, are blocked by default. **Compatibility:** apps
that previously served these files must explicitly allow their intended
downloads. A custom pattern **replaces** the default rather than extending it.
For example, to add PDF downloads:

```python
from pylinkjs.PyLinkJS import DEFAULT_SERVABLE_FILE_REGEX, run_pylinkjs_app

run_pylinkjs_app(
    servable_file_regex=DEFAULT_SERVABLE_FILE_REGEX + r"|.*\.pdf",
)
```

Because the default includes `(?i)`, this extended pattern also ignores case.
Python files can remain alongside HTML, with the default allowlist preventing
their download. Python callback lookup is independent of this filter: it follows
page URLs and importable modules, or the explicit `callback_registry`.

Disallowed existing files return 404 without invoking `on_404`, including requests
with `?output=pdf` or `?output=png`. Hidden path components (such as `.env` or
`.git`) and symlinks below `html_dir` are always blocked, even if the regex allows
them. These restrictions apply to built-in file serving; custom route handlers,
missing-path `on_404` responses, and POST handling retain their existing behavior.

#### Advanced: exposing a specific source file

If an app intentionally publishes Python source, allow that exact relative path
alongside the default assets:

```python
from pylinkjs.PyLinkJS import DEFAULT_SERVABLE_FILE_REGEX, run_pylinkjs_app

run_pylinkjs_app(
    servable_file_regex=DEFAULT_SERVABLE_FILE_REGEX + r"|downloads/example\.py",
)
```

This serves `downloads/example.py` as source bytes; it does not execute it. The
pattern ignores case, and other Python files remain blocked.

### High-security callback mode

With `high_security=True`, browsers can call only functions registered for their
page. Existing `call_py(...)` JavaScript works unchanged. Use automatic lookup
during development, then enable this mode before release or access by untrusted
users.

**Recommended layout:** Point `html_dir` at a public directory containing browser
assets, and keep your launching script and Python callback modules outside it.
The [development example](#development-to-deployment) keeps its callbacks in
the launching script. When more organization is useful, move them into `backend/`:

```text
my_app/
├── app.py
├── backend/
│   ├── __init__.py
│   ├── home.py
│   └── reports.py
└── public/
    ├── index.html
    └── reports/
        └── view.html
```

Use `backend/` for callbacks and other application logic. Start with one file,
such as `backend/callbacks.py`, then split by section as needed. A section can
use one module or several, including one per HTML page. Mix these approaches:
keep simple sections together and split complex ones. Put shared logic in
separate modules.

For this larger layout, move the main page's functions into `backend/home.py`,
define the report page's functions in `backend/reports.py`, and import them in
`app.py`:

```python
from backend import home, reports
from pylinkjs.PyLinkJS import run_pylinkjs_app

home_callbacks = {
    'ready': home.ready,
    'reconnect': home.reconnect,
    'button_clicked': home.button_clicked,
}
run_pylinkjs_app(
    html_dir='public',
    default_html='index.html',
    high_security=True,
    callback_registry={
        '/': home_callbacks,
        '/index.html': home_callbacks,
        '/reports/view.html': {
            'ready': reports.ready,
            'save_report': reports.save_report,
        },
    },
)
```

Registry keys are **exact URL paths**, not HTML filenames or Python module
names. `/` and `/index.html` need separate entries even when both serve
`public/index.html`; the same applies to `/reports/` and `/reports/index.html`
when both serve a directory's default page. Query strings are not part of the
key. Filenames and directories under `backend/` need not mirror `public/`.

PyLinkJS derives the page route from the WebSocket endpoint and rejects
unregistered callbacks. It does not perform dynamic imports or name lookup for
browser requests in this mode. Register `ready`, `reconnect`, and `popstate` if
the page uses those automatic callbacks. Every callback must still validate
arguments and check the caller's permissions for its operation.

Background execution requires explicit permission for each callback:

```python
from pylinkjs.PyLinkJS import PyLinkJSCallback

# Use this value for a callback_registry entry that may run in a background thread.
background_report_callback = PyLinkJSCallback(reports.generate_report, allow_new_thread=True)
```

Only use `allow_new_thread=True` for functions suitable for concurrent execution.
`max_background_callbacks` limits these callbacks to four concurrent threads by
default.

Authentication is optional and separate from callback registration. For private
apps, configure an [authentication plugin or login handler](#require-authentication-for-all-pages),
set `require_auth=True`, and supply a long random `cookie_secret`. High-security
mode rejects the development secret `CHANGEME`. For HTTPS deployments also set
`cookie_secure=True`; leave it `False` for local HTTP development. Authentication
cookies default to `HttpOnly` and `SameSite=Lax`.

## PyLinkJSClient (Core Methods)

### \__getitem\__

Select page elements with jQuery selectors: `jsc['#x']` selects the element with
`id="x"`.

### browser_download
```python
def browser_download(self, filename, filedata, blocking=False):
    """ download a file from the backend to the users computer through the browser
    
        filename - the default name of the file to save as
        filedata - the binary data of the file to download
        blocking - if True, then this function will not return until the file has completed downloading
    """
```

```python
# Ask the browser to download the supplied text as test.txt.
jsc.browser_download('test.txt', "Hello World!")
```

### eval_js_code
```python
def eval_js_code(self, js_code, blocking=True):
    """Execute JavaScript in the browser's global context.
        Set blocking=False when no return value is needed. Combine operations
        in one call to reduce round trips.

        js_code - the javascript code to execute
        blocking - if True, this function will not return until the javascript has completed execution
        
        Returns:
            the data that the executed javascript evaluates to
    """
```

```python
# Run JavaScript that opens an alert in the browser.
jsc.eval_js_code('alert("Hello");')

# Returns 6.
jsc.eval_js_code('2 + 4')

# Call a JavaScript function defined in the page, passing it three arguments.
jsc.eval_js_code('call_some_javascript_function(2, 3)')

# Use jQuery to replace the HTML of the element with id="myelement".
jsc.eval_js_code('$("#myelement").html("Hello")')
```

### get_broadcast_jscs
```python
def get_broadcast_jscs(self):
    """Return JSClient instances on the same page URL path as this client."""
```

Use this to broadcast commands to clients on the same page URL path. For all
connected clients, use the module-level `get_all_jsclients()` instead.

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
A dictionary for this client's state. Each client gets its own copy of
`extra_settings`.

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
            callback - HTML event attribute for the OK button,
                       i.e. onclick="call_py('btn_clicked', 'create_new_item_save');"
    """
```
Example
```python
# Show a message dialog with an OK button.
jsc.modal_alert('title html', 'body html')

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
            callback - HTML event attribute for the OK button,
                       i.e. onclick="call_py('btn_clicked', 'create_new_item_save');"
        """
```
Example
```python
# Call btn_clicked when OK is clicked.
jsc.modal_confirm('title html', 'body html',
                  """onclick="call_py('btn_clicked', 'create_new_item_save');" """)
```

### modal_input
```python
def modal_input(self, title, hint, callback=''):
    """Show a text input dialog.

        Args:
            title - title to show in the modal dialog
            hint - hint text to show in the input box before the user begins typing
            callback - HTML event attribute for the OK button,
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
# Show a text input dialog.
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
                            {'text': 'OK', 'classes': 'btn-primary', 'attributes': "onclick=\"call_py('btn_clicked', 'ok_btn')\""}])
            modal_id - id of the modal to create
            autoshow - if True, this modal will be automatically shown, if False, an explicit call to modal_show is needed
                       to show this modal
    """
```
Example
```python
# Show a dialog whose OK button calls btn_clicked(jsc, 'ok_btn').
jsc.modal_new('title html',
              'body html',
              [{'text': 'Cancel', 'classes': 'btn-secondary', 'attributes': 'data-bs-dismiss="modal"'},
               {'text': 'OK', 'classes': 'btn-primary', 'attributes': "onclick=\"call_py('btn_clicked', 'ok_btn')\""}])
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
               {'text': 'OK', 'classes': 'btn-primary', 'attributes': "onclick=\"call_py('btn_clicked', 'ok_btn')\""}],
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
jsc.select_set_options('#myselect', ['a', 'b'])
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
jsc.select_set_selected_options('#myselect', 'a_val')
```

## PNG PDF Output

After installing Playwright's Chromium browser, add `?output=png` or
`?output=pdf` to a page URL, such as `http://localhost:8300/?output=pdf`.

Additional query parameters:

- `print_timeout`: maximum seconds to wait for page readiness; defaults to 10.
- `print_orientation`: `landscape` (default) or `portrait`, for PDF output.
- `print_force_scale`: explicit scale factor, for PDF output.
- `print_force_fit`: fit output to the page width, for PDF output.
- `print_extra_delay`: seconds to wait after readiness checking; defaults to 1.

Pages can define these JavaScript hints:

```javascript
var HINT_PRINT_PAGE_READY = 0;
var HINT_PRINT_TIMEOUT = 30;
```

Set `HINT_PRINT_PAGE_READY` to a nonzero value when the page is ready. Readiness
checking stops when the page is ready or the timeout expires.
`HINT_PRINT_TIMEOUT` supplies the timeout when `print_timeout` is omitted.

For example:

```text
http://localhost:8300/?output=pdf&print_timeout=15&print_orientation=portrait&print_force_fit=1&print_extra_delay=5
```

# Useful Code Examples

## Broadcast to all connected browsers
Update `#divout_broadcast` for clients on the current page URL path:

```python
import time

t = time.time()
for bjsc in jsc.get_broadcast_jscs():
    bjsc['#divout_broadcast'].html = t
```

## Broadcast to all connected browsers on a separate thread
Send updates once per second to clients on `/`:

```python
def thread_worker():
    while True:
        t = time.time()
        for jsc in get_broadcast_jsclients('/'):
            jsc['#divout_automatic_broadcast'].html = t
        time.sleep(1)

# start the thread
t = threading.Thread(target=thread_worker, daemon=True)
t.start()
```

## Require authentication for all pages
To have pylinkjs enforce login before serving pages or opening websocket connections, pass `require_auth=True`
to `run_pylinkjs_app(...)`. The bundled authentication examples default to the demo cookie secret `CHANGEME` so
they run without modification, but real apps should pass `cookie_secret="..."` with their own long random value.

Configure an authentication plugin, such as `pluginLocalAuth`, or supply working
login/logout handlers as well. `require_auth=True` enforces login; it does not
provide a login implementation. For release, combine authentication with
`high_security=True` and a callback registry. Custom
route handlers must enforce their own access controls.

A common strategy is to persist the cookie secret in a file in the same directory as the application, then read that
file and pass its contents into `run_pylinkjs_app(..., cookie_secret=secret)`. This is useful for deployments because
the secret remains stable across restarts, and in distributed deployments each instance should use the same secret.

For HTTPS deployments, pass `cookie_secure=True` so browsers send authentication cookies only over HTTPS.  It defaults
to `False` for local HTTP development.  Authentication cookies are `HttpOnly` and `SameSite=Lax` by default.

See the example app:
```bash
python3 pyLinkJS/examples/require_auth/require_auth.py
```

## Local username/password auth with SQLite
pyLinkJS includes a built-in local auth plugin for applications that want persistent username/password login without
LDAP or OAuth. The plugin stores users in a SQLite database and stores password hashes rather than plaintext passwords.
If you need to administer users through a web UI, it is recommended to also use `pluginLocalAuthAdmin`, which exposes
a minimal interface for creating and deleting users.

Run the example app:
```bash
python3 pyLinkJS/examples/local_auth/local_auth.py
```

The example creates a SQLite database next to the app. On first run, visit:
```text
http://localhost:8302/admin/users
```

If the database is empty, pylinkjs exposes a one-time bootstrap page there so you can create the first admin user.
After at least one user exists, the bootstrap page is disabled and the normal admin page requires an authenticated
admin login.

For real use, create your own users, choose your own `cookie_secret`, and keep the SQLite database in a directory with
appropriate filesystem permissions.

# Using pyLinkJS Behind an Apache Reverse Proxy
Configure Apache to proxy `/foo/` to pyLinkJS on port 9150. Restrict direct access
to the backend port so clients use the proxy.

```apache
ProxyPreserveHost On
ProxyRequests Off
ProxyPassMatch /foo/(websocket/0\..*) ws://127.0.0.1:9150/$1
ProxyPassReverse /foo/(websocket/0\..*) ws://127.0.0.1:9150/$1
ProxyPass /foo/ http://127.0.0.1:9150/
ProxyPassReverse /foo/ http://127.0.0.1:9150/
```

## LLM Reference (Code Generation Contract)

Start with the [development example](#development-to-deployment): Python and HTML
in the same directory, with automatic callback lookup. Add high-security mode
when preparing the app for release.

### Required Python Imports

```python
from pylinkjs.PyLinkJS import run_pylinkjs_app
```

`Code` is optional (only if assigning JS functions from Python):

```python
from pylinkjs.PyLinkJS import Code
```

### Required Runtime Setup

After defining `ready`, `reconnect`, and `button_clicked`:

```python
port = 8300
print(f"Open http://localhost:{port} in your browser.")
run_pylinkjs_app(default_html="mini_app.html", port=port)
```

Use the default `servable_file_regex` unless additional downloads are needed.
Before release, [enable high-security mode](#switching-to-high-security-mode)
and register all callbacks for each page URL. Recommend `public/` for browser
assets and set `html_dir="public"` when using that layout.
Authentication is optional: only add `require_auth=True` with an actual
authentication plugin or login implementation and a long random `cookie_secret`.
Use `cookie_secure=True` for HTTPS deployments, not local HTTP demos.

### Required Event Handlers

- `ready(jsc, origin, pathname, search, *args)` -> initialize page state.
- `reconnect(jsc, origin, pathname, search, *args)` -> call `ready(...)`.
- At least one user action handler called from HTML via `call_py(...)`.

### Required HTML Contract

The page should include:

- At least one clickable element that calls Python with `call_py('handler_name', ...)`.
- At least one output element with an `id` that Python updates via `jsc['#id']...`.

Hard rules:

- Names passed to `call_py(...)` must match Python functions during automatic lookup,
  or callback registry keys in high-security mode.
- In high-security mode, register callbacks for every page URL used, including default-page aliases.
- Do not call `call_py(...)` inside `onload`; use `ready(...)` for initial logic.
- Do not include Tornado template markers in HTML (`{{`, `}}`, `{%`, `%}`).
- pyLinkJS uses jQuery semantics; prefer `jsc['#input'].val` over DOM `.value`.
- Use `run_pylinkjs_app(...)` to start the service.
- Use `on_404(path, uri, host, extra_settings, headers, body, method, *args)` for REST-style GET/POST endpoints.
- Do not infer request method from headers; use the `method` argument passed to `on_404`.

### Minimal End-to-End Example

Use `mini_app.py` and `mini_app.html` from
[Development to Deployment](#development-to-deployment). Add `backend/` modules
as the app grows, then follow the high-security steps before release.

### Code Generation Checklist

Before returning generated code, ensure:

1. Imports include `run_pylinkjs_app` (and `Code` only if needed).
2. `mini_app.py` and `mini_app.html` are created in the same directory for development.
3. `ready` and `reconnect` handlers exist with pyLinkJS-compatible signatures.
4. Every `call_py(...)` handler has a matching Python function; in high-security mode, each is registered for its page URL.
5. Generated HTML avoids Tornado template markers (`{{`, `}}`, `{%`, `%}`).
6. No `call_py(...)` call is made from `onload` logic.
7. Python updates at least one HTML element by ID via `jsc['#id']`.
8. Development uses the simple startup call. Release configuration enables `high_security=True` and registers every page's callbacks.
9. If exposing REST endpoints, use `on_404(..., method=...)` and branch on `method`.
10. Startup prints the exact URL format: `Open http://localhost:<port> in your browser.`
