# --------------------------------------------------
#    Imports
# --------------------------------------------------
import logging
import numpy as np
import pandas as pd
from pylinkjs.PyLinkJS import run_pylinkjs_app
from pylinkjs.plugins.bokehPlugin import pluginBokeh


# --------------------------------------------------
#    Globals
# --------------------------------------------------
INITIAL_DF = pd.DataFrame(np.random.randint(0,100,size=(4, 3)), columns=list('ABC'))

# --------------------------------------------------
#    Functions
# --------------------------------------------------
def get_data(**kwargs):
    if kwargs['name'] == 'chart_sample_hbar':
        return INITIAL_DF
    if kwargs['name'] == 'chart_sample_line':
        return INITIAL_DF
    if kwargs['name'] == 'chart_sample_pie':
        return INITIAL_DF
    if kwargs['name'] == 'chart_sample_table':
        return INITIAL_DF
    if kwargs['name'] == 'chart_sample_vbar':
        return INITIAL_DF


# --------------------------------------------------
#    Event Handlers
# --------------------------------------------------
def btn_refresh_data_clicked(jsc):
    """ simple example of a button click """
    # update with random data
    df = pd.DataFrame(np.random.randint(0,100,size=(4, 3)), columns=list('ABC'))

    # update the data
    jsc['#df_display'].html = df.to_string()
    jsc.update_chart('chart_sample_hbar', df)
    jsc.update_chart('chart_sample_line', df)
    jsc.update_chart('chart_sample_pie', df)
    jsc.update_chart('chart_sample_table', df)
    jsc.update_chart('chart_sample_vbar', df)


def ready(jsc, *args):
    """ called when a webpage creates a new connection the first time on load """
    jsc['#df_display'].html = INITIAL_DF.to_string()


# --------------------------------------------------
#    Main
# --------------------------------------------------
def main():
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

if __name__ == '__main__':
    main()

