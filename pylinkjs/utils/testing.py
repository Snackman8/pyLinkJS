import os
import time
import inspect
from threading import Thread
import urllib


import socket
from contextlib import closing


def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def download_and_compare(server_func, url, update_truth=False, truth_path='.', print_extra_delay=1):
    # start server with free port
    port = find_free_port()
    t = Thread(target=server_func, args=({'port': port},))
    t.daemon = True
    t.start()
    
    # convert url to use free port
    parsed_url = urllib.parse.urlparse(url)
    url = parsed_url._replace(netloc=parsed_url.netloc + f':{port}').geturl()
    
    # add the output type of png
    if '?' in url:
        url = url + f'&output=png&print_extra_delay={print_extra_delay}'
    else:
        url = url + f'?output=png&print_extra_delay={print_extra_delay}'
    
    # render the url
    time.sleep(1)
    print(url)
    img = urllib.request.urlopen(url)
    png = img.read()

    # get the calling function name
    func_name = inspect.stack()[1][3]
    
    # init
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
    