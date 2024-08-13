# --------------------------------------------------
#    Imports
# --------------------------------------------------
from contextlib import closing
import os
import time
import inspect
from io import BytesIO
from PIL import Image, ImageChops, ImageDraw
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import socket
from threading import Thread
import urllib


# --------------------------------------------------
#    Helper Functions
# --------------------------------------------------
def _find_free_port():
    """ return a free socket port number that is currently not in use """
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def _start_pylinkjs_app(server_func, url, server_func_args):
    """ start a pylink js app in a separate thread using a new unused port

        Args:
            server_func - function to call to start the application, i.e. main
            url - url to call to access the started application, i.e. http://localhost
            server_func_args - arguments to pass into the function

        Returns:
            tuple of thread running the application and url including port number
     """
    # start server with free port
    port = _find_free_port()
    server_func_args['port'] = port
    t = Thread(target=server_func, args=(server_func_args,))
    t.daemon = True
    t.start()

    # convert url to use free port
    parsed_url = urllib.parse.urlparse(url)
    url = parsed_url._replace(netloc=parsed_url.netloc + f':{port}').geturl()

    # success!
    return t, url


def _perform_comparison(truth_path, update_truth, png):
    """ perform comparision between png and truth
        assert fails if test does not match truth

        Args:
            truth_path - path to truth file
            update_truth - if True, truth file will be overwritten
            png - png binary generated from the test
    """
    # init
    func_name = inspect.stack()[2][3]
    truth_filepath = os.path.join(
        os.path.abspath(os.path.dirname(truth_path)), f"truth_{func_name}.png"
    )
    test_filepath = os.path.join(
        os.path.abspath(os.path.dirname(truth_path)), f"test_{func_name}.png"
    )
    xor_filepath = os.path.join(
        os.path.abspath(os.path.dirname(truth_path)), f"test_{func_name}_xor.png"
    )

    # write truth if needed
    if update_truth:
        with open(truth_filepath, "wb") as f:
            f.write(png)

    # read the truth file
    try:
        with open(truth_filepath, "rb") as f:
            truth_png = f.read()
    except:
        truth_png = b''

    # perform comparison
    im1 = Image.open(BytesIO(png))
    im2 = Image.open(BytesIO(truth_png))
    im_xor = ImageChops.difference(im1, im2)

    # perform comparison
    same = im_xor.getbbox()
    if same is not None:
        with open(test_filepath, "wb") as f:
            f.write(png)
        im_xor.save(xor_filepath, format='PNG')
    else:
        if os.path.exists(test_filepath):
            os.remove(test_filepath)
        if os.path.exists(xor_filepath):
            os.remove(xor_filepath)

    assert same is None


def _process_redacted(png, redacted):
    """ draw black redacted squares on the png

        Args:
            png - png to draw on
            redacted - list of rectangle coordinates (x, y, w, h) to redact, i.e. [[0, 0, 50, 100], [200, 200, 10, 100]]

        Returns:
            modified png
    """
    # convert base64 to PIL Image
    im = Image.open(BytesIO(png))
    im_draw = ImageDraw.Draw(im)

    for r in redacted:
        x, y, w, h = r
        im_draw.rectangle([x, y, x + w, y + h], fill ="black", outline ="red")

    # save
    buf = BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()




# --------------------------------------------------
#    Functions
# --------------------------------------------------
def download_and_compare(server_func, url, server_func_args={}, update_truth=False, truth_path='.', print_extra_delay=1, print_timeout=5, redacted=[]):
    """
        run an application and download the png of the finished application.  Compare with truth

        Args:
            server_func - function to run to start application
            url - url to call for testing, i.e. http://localhost
            server_func_args - dictionary of arguments to pass into the server function
            update_truth - if set to True, the truth file will automatically be updated
            truth_path - path to look for truth files
            print_extra_delay - how many seconds to wait after printing is complete before capturing png
            print_timeout - maximum time to wait for printing to complete
            redacted - list of rectangle coordinates (x, y, w, h) to redact, i.e. [[0, 0, 50, 100], [200, 200, 10, 100]]
    """
    # start the app
    _t, url = _start_pylinkjs_app(server_func, url, server_func_args)

    # add the output type of png
    if '?' in url:
        url = url + f'&output=png&print_extra_delay={print_extra_delay}&print_timeout={print_timeout}'
    else:
        url = url + f'?output=png&print_extra_delay={print_extra_delay}&print_timeout={print_timeout}'

    # render the url
    time.sleep(1)
    img = urllib.request.urlopen(url)
    png = img.read()

    # process redacted sections
    png = _process_redacted(png, redacted)

    # perform comparison
    _perform_comparison(truth_path, update_truth, png)


def selenium_test_begin(server_func, url, server_func_args={}, browser_options=[]):
    # start the app
    _t, url_with_port = _start_pylinkjs_app(server_func, url, server_func_args)

    # start selenium
    chrome_options = Options()

    headless_present = False
    for opt in browser_options:
        if opt ==  '--headless=no':
            headless_present = True
        else:
            chrome_options.add_argument(opt)
    if not headless_present:
        chrome_options.add_argument("--headless=new") # for Chrome >= 109
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url_with_port)
    time.sleep(1)

    return driver, url_with_port


def selenium_test_compare_and_finish(driver, update_truth=False, truth_path='.', redacted=[], sleep_time=1):
    # get screenshot
    time.sleep(sleep_time)
    png = driver.get_screenshot_as_png()
    driver.quit()

    # process redacted sections
    png = _process_redacted(png, redacted)

    # perform comparison
    _perform_comparison(truth_path, update_truth, png)
