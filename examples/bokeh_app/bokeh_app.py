# --------------------------------------------------
#    Imports
# --------------------------------------------------
import logging
import numpy as np
import pandas as pd
from pylinkjs.PyLinkJS import run_pylinkjs_app
from pylinkjs.plugins.bokehPlugin import pluginBokeh


# --------------------------------------------------
#    Functions
# --------------------------------------------------
def get_data(**kwargs):
    if kwargs['name'] == 'chart_sample_line':
        # update with random data
        df = pd.DataFrame(np.random.randint(0,100,size=(4, 2)), columns=list('AB'))
        return df


# --------------------------------------------------
#    Event Handlers
# --------------------------------------------------
def button_clicked(jsc, a, b, c):
    """ simple example of a button click """
    # update with random data
    df = pd.DataFrame(np.random.randint(0,100,size=(4, 2)), columns=list('AB'))
    jsc.update_chart('chart_sample_line', df)


# --------------------------------------------------
#    Main
# --------------------------------------------------
if __name__ == '__main__':
    # configure logger
    logging.basicConfig(level=logging.DEBUG, format='%(relativeCreated)6d %(threadName)s %(message)s')

    # define the port
    port = 8300

    # init the google oauth2 plugin
    bokeh_plugin = pluginBokeh(get_data_handler=get_data)

    # run the application
    run_pylinkjs_app(default_html='bokeh_app.html',
                     port=port,
                     plugins=[bokeh_plugin])
