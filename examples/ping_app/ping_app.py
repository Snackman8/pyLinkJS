# --------------------------------------------------
#    Imports
# --------------------------------------------------
import argparse
import logging
import os
from pylinkjs.PyLinkJS import run_pylinkjs_app
import business_logic


# --------------------------------------------------
#    Handlers
# --------------------------------------------------
def ready(jsc, *args):
    """ called when a webpage creates a new connection the first time on load """

    # handle when the /random_data page loads
    computer_ips = business_logic.get_computer_ips()

    if args[1] == '/':
        # look at data and generate filter options
        computer_names = sorted(computer_ips.keys())
        jsc.select_set_options('#select_host', computer_names)
        select_host_changed(jsc)


def button_ping_clicked(jsc):
    """ simple example of a button click """
    # get the computer ip addresses
    computer_ips = business_logic.get_computer_ips()

    # get the computer name from the drop down
    computer_name = jsc.select_get_selected_options('#select_host')[0][0]
    ip_address = computer_ips[computer_name]
    html = f'Beginning ping test to ({computer_name}) {ip_address}...\n'
    jsc['#divout'].html = f'<pre>{html}</pre>'
    jsc.eval_js_code("""$("*").css("cursor", "progress");""")
    response = os.system("ping -c 1 -W1 " + ip_address + " > /dev/null 2>&1")
    jsc.eval_js_code("""$("*").css("cursor", "default");""")
    if response == 0:
        html = html + '<span class=success>PING SUCCEEDED!  COMPUTER IS ONLINE!</span>\n'
    else:
        html = html + '<span class=failure>PING FAILED!</span>\n'
    jsc['#divout'].html = f'<pre>{html}</pre>'


def select_host_changed(jsc):
    computer_ips = business_logic.get_computer_ips()
    computer_name = jsc.select_get_selected_options('#select_host')[0][0]
    ip_address = computer_ips[computer_name]
    jsc['#ip_address'].html = ip_address


# --------------------------------------------------
#    Main
# --------------------------------------------------
if __name__ == '__main__':
    # setup the logger
    logging.basicConfig(level=logging.DEBUG, format='%(relativeCreated)6d %(threadName)s %(message)s')
    
    # handle the --port argument
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, required=False, default=8300)
    args = vars(parser.parse_args())

    # run the app
    run_pylinkjs_app(default_html='ping_app.html', html_dir=os.path.dirname(__file__), internal_polling_interval=0.025, port=args['port'], app_mode=True, app_top=100, app_left=100, app_width=800, app_height=520)
