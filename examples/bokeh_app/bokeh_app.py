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
def refresh_charts(jsc, columns = 3):
    # create a random dataframe
    rows = np.random.randint(4, 10)
    column_headers = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ'[:columns])
    df = pd.DataFrame(np.random.randint(0,100,size=(rows, columns)), columns=column_headers)

    jsc['#chart_line_df'].html = df.to_string()
    jsc.update_chart('chart_line', df)
    jsc['#chart_pie_df'].html = df.head(1).to_string()
    jsc.update_chart('chart_pie', df.head(1))
    jsc['#chart_hbar1_df'].html = df.head(1).to_string()
    jsc.update_chart('chart_hbar1', df.head(1))
    jsc['#chart_hbar_df'].html = df.to_string()
    jsc.update_chart('chart_hbar', df)
    jsc['#chart_vbar1_df'].html = df.head(1).to_string()
    jsc.update_chart('chart_vbar1', df.head(1))
    jsc['#chart_vbar_df'].html = df.to_string()
    jsc.update_chart('chart_vbar', df)
    jsc['#chart_table_df'].html = df.to_string()
    jsc.update_chart('chart_table', df)
    jsc['#chart_boxplot_df'].html = df.to_string()
    jsc.update_chart('chart_boxplot', df)

    # special for pie chart
    df_pie = df.head(1).copy()
    for c in df_pie.columns:
        df_pie.loc['text', c] = c + ' ' + c
    jsc['#chart_pie_df'].html = df_pie.to_string()
    jsc.update_chart('chart_pie', df_pie)
    
    # histogram data and update
    bins = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ'[:columns])
    df_hist = pd.DataFrame(index=bins)
    for b in bins:
        df_hist.loc[b, 'counts'] = np.random.randint(0, 100)
        df_hist.loc[b, 'bin_text'] = b + ' ' + b
    df_hist['counts'] = df_hist['counts'].astype('int')     
    
    jsc['#chart_histogram_df'].html = df_hist.to_string()
    jsc.update_chart('chart_histogram', df_hist)
    

def ready(jsc, *args):
    """ called when a webpage creates a new connection the first time on load """
    refresh_charts(jsc)


# --------------------------------------------------
#    Main
# --------------------------------------------------
def main():
    # configure logger
    logging.basicConfig(level=logging.DEBUG, format='%(relativeCreated)6d %(threadName)s %(message)s')

    # define the port
    port = 8300

    # init the google oauth2 plugin
    bokeh_plugin = pluginBokeh()

    # run the application
    run_pylinkjs_app(default_html='bokeh_app.html',
                     port=port,
                     plugins=[bokeh_plugin])

if __name__ == '__main__':
    main()
