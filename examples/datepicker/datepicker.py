import datetime
import logging
from pylinkjs.PyLinkJS import run_pylinkjs_app


def ready(jsc, *args):
    """ called when a webpage creates a new connection the first time on load """
    # handle when the page loads
    if args[1] == '/':
        # set the datepicker to todays date when the page loads
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        jsc.eval_js_code(f"$('#datepick').val('{today}')")
        

def button_clicked(jsc):
    """ simple example of a button click """
    datepick = jsc.eval_js_code("$('#datepick').val()")

    jsc['#divout'].html = f"Date on the web page is {datepick}"


if __name__ == '__main__':
    # start the thread and the app
    logging.basicConfig(level=logging.DEBUG, format='%(relativeCreated)6d %(threadName)s %(message)s')
    run_pylinkjs_app(default_html='datepicker.html')
