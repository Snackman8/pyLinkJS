# --------------------------------------------------
#    Imports
# --------------------------------------------------
import logging
from urllib.parse import urlparse, parse_qs
import pretty_html_table
import business_logic
from pylinkjs.PyLinkJS import run_pylinkjs_app, execute_in_subprocess


# --------------------------------------------------
#    Constants
# --------------------------------------------------
PORT = 9150


# --------------------------------------------------
#    Handlers
# --------------------------------------------------
def ready(jsc, *args):
    """ called when a webpage creates a new connection the first time on load """

    # handle when the /random_data page loads
    if args[1] == '/random_data.html':
        # look at data and generate filter options
        jsc.select_set_options('#select_rows', [[10, '10 rows'], [20, '20 rows'], [30, '30 rows']])
        jsc.select_set_options('#select_cols', [[3, '3 cols'], [6, '6 cols'], [9, '9 cols']])


def btn_get_data_random_data(jsc, *args):
    # change to wait cursor
    jsc.eval_js_code("""$("*").css("cursor", "progress");""")
    jsc['#data_div'].html = '<span style="color:orange">Geting Data, this may take a while...</span>'

    # get the rows and columns value from the web page
    rows = jsc.select_get_selected_options('#select_rows')
    cols = jsc.select_get_selected_options('#select_cols')

    # if multiple items are selected in the dropdown, we only want the first one
    rows = rows[0]
    cols = cols[0]

    # we want the value of the selected item, not the display text
    rows = rows[0]
    cols = cols[0]

    # convert to integer
    rows = int(rows)
    cols = int(cols)

    # generate the random data
    #
    #    Execute the get_random_data in a seperate process on a different core
    #
    df_data = execute_in_subprocess(business_logic.get_random_data, rows, cols)

    # convert the dataframe to pretty html
    html = pretty_html_table.build_table(df_data, 'blue_light')

    # push the random data to the web page
    jsc['#data_div'].html = html

    # change to default cursor
    jsc.eval_js_code("""$("*").css("cursor", "default");""")


def handle_404(path, uri, *args):
    # handle URLS that do not have html pages
    if path.startswith('random_data.html/csv'):
        # init
        content_type = 'text/plain'
        status_code = 200

        # parse the URL
        parts = urlparse(uri)
        params = parse_qs(parts.query)

        # extract parameters
        rows = int(params['rows'][0])
        cols = int(params['cols'][0])

        # generate the random data
        #
        #    Execute the get_random_data in a seperate process on a different core
        #
        df_data = execute_in_subprocess(business_logic.get_random_data, rows, cols)

        # convert the dataframe to pretty html
        html = df_data.to_csv()

        # return the data to the handler
        return (html, content_type, status_code)


# --------------------------------------------------
#    Main
# --------------------------------------------------
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(relativeCreated)6d %(threadName)s %(message)s')
    run_pylinkjs_app(default_html='index.html', on_404=handle_404, port=PORT)
