# --------------------------------------------------
#    Imports
# --------------------------------------------------
from contextlib import closing
import os
import time
import inspect
from io import BytesIO
from PIL import Image, ImageDraw
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


def _start_pylinkjs_app(server_func, url):
    """ start a pylink js app in a separate thread using a new unused port

        Args:
            server_func - function to call to start the application, i.e. main
            url - url to call to access the started application, i.e. http://localhost

        Returns:
            tuple of thread running the application and url including port number
     """
    # start server with free port
    port = _find_free_port()
    t = Thread(target=server_func, args=({'port': port},))
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
    same = truth_png == png
    if not same:
        with open(test_filepath, "wb") as f:
            f.write(png)
    else:
        if os.path.exists(test_filepath):
            os.remove(test_filepath)

    assert same


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


def download_and_compare(server_func, url, update_truth=False, truth_path='.', print_extra_delay=1, print_timeout=5, redacted=[]):
    """
        run an application and download the png of the finished application.  Compare with truth

        Args:
            server_func - function to run to start application
            url - url to call for testing, i.e. http://localhost
            update_truth - if set to True, the truth file will automatically be updated
            truth_path - path to look for truth files
            print_extra_delay - how many seconds to wait after printing is complete before capturing png
            print_timeout - maximum time to wait for printing to complete
            redacted - list of rectangle coordinates (x, y, w, h) to redact, i.e. [[0, 0, 50, 100], [200, 200, 10, 100]]
    """
    # start the app
    _t, url = _start_pylinkjs_app(server_func, url)

    # add the output type of png
    if '?' in url:
        url = url + f'&output=png&print_extra_delay={print_extra_delay}&print_timeout={print_timeout}'
    else:
        url = url + f'?output=png&print_extra_delay={print_extra_delay}&print_timeout={print_timeout}'

    # render the url
    time.sleep(1)
    print(url)
    img = urllib.request.urlopen(url)
    png = img.read()

    # process redacted sections
    png = _process_redacted(png, redacted)

    # perform comparison
    _perform_comparison(truth_path, update_truth, png)


# --------------------------------------------------
#    Functions
# --------------------------------------------------
def download_and_compare_selenium(server_func, url, exercise_func, update_truth=False, truth_path='.', redacted=[]):
    """
        run an application and download the png of the finished application.  Exercise using selenium, compare with truth

        Args:
            server_func - function to run to start application
            url - url to call for testing, i.e. http://localhost
            exercise_func - function to call to exercise the application using selenium.  prototype is f(driver, url)
            update_truth - if set to True, the truth file will automatically be updated
            truth_path - path to look for truth files
            redacted - list of rectangle coordinates (x, y, w, h) to redact, i.e. [[0, 0, 50, 100], [200, 200, 10, 100]]
    """
    # start the app
    _t, url = _start_pylinkjs_app(server_func, url)

    # start selenium
    chrome_options = Options()
    chrome_options.add_argument("--headless=new") # for Chrome >= 109
    driver = webdriver.Chrome(options=chrome_options)

    # exercise the app
    driver.get(url)
    exercise_func(driver, url)

    # get screenshot
    png = driver.get_screenshot_as_png()
    driver.quit()

    # process redacted sections
    png = _process_redacted(png, redacted)

    # perform comparison
    _perform_comparison(truth_path, update_truth, png)
