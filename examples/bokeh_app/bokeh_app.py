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
DATA_CACHE = {}

# --------------------------------------------------
#    Functions
# --------------------------------------------------
def get_data(jsc_id, jsc_sequence_number, **kwargs):
    if jsc_id not in DATA_CACHE:
        print('Creating cache continer', jsc_id)
        DATA_CACHE[jsc_id] = {'sequence_number': -1}
    if DATA_CACHE[jsc_id]['sequence_number'] != jsc_sequence_number:
        # invalidate the data cache and incremenet to the new sequence number
        print ('Cache Invalidate  ', DATA_CACHE[jsc_id]['sequence_number'], jsc_sequence_number)
        for k in list(DATA_CACHE[jsc_id].keys()):
            del DATA_CACHE[jsc_id][k]
        DATA_CACHE[jsc_id]['sequence_number'] = jsc_sequence_number

    if 'cached_chart_data' not in DATA_CACHE[jsc_id]:
        print ('Cache Miss', jsc_id, jsc_sequence_number)
        columns = kwargs.get('columns', 3)
        rows = np.random.randint(4, 10)

        # generate some fake column headers using the letters of the alphabet
        column_headers = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ'[:columns])

        DATA_CACHE[jsc_id]['cached_chart_data'] = pd.DataFrame(np.random.randint(0,100,size=(rows, columns)), columns=column_headers)
    else:
        print ('Cache Hit', jsc_id, jsc_sequence_number)

    df = DATA_CACHE[jsc_id]['cached_chart_data']

    if kwargs['name'] == 'df_display':
        return df
    if kwargs['name'] == 'chart_sample_hbar':
        return df
    if kwargs['name'] == 'chart_sample_vbar':
        return df
    if kwargs['name'] == 'chart_sample_line':
        return df
    if kwargs['name'] == 'chart_sample_pie':
        return df
    if kwargs['name'] == 'chart_sample_table':
        return df

    # histogram data
    bins = ['<55%', '55%-65%', '65%-75%', '75%-85%', '85%-95%', '95%-105%', '105%-115%', '115%-125%', '125%-135%', '135%-145%', '145%-155%', '>155%']
    df_hist = pd.DataFrame(index=bins)
    for b in bins:
        df_hist.loc[b, 'counts'] = np.random.randint(0, 100)
        df_hist['bin_text'] = df_hist['counts']

    if kwargs['name'] == 'chart_histogram_table':
        return df_hist.reset_index()

    if kwargs['name'] == 'chart_sample_histogram':
        return df_hist


# --------------------------------------------------
#    Event Handlers
# --------------------------------------------------
def on_context_close(jsc):
    print('CONTEXT CLOSE deleting cache', jsc.get_id())
    del DATA_CACHE[jsc.get_id()]

def on_context_open(jsc):
    print ('CONTEXT OPEN', jsc.get_id())

def btn_refresh_charts_with_new_data_clicked(jsc, columns):
    """ refresh charts with new data, invalidate the data cache to retrieve new data """
    # invalidate the cache
    jsc.increment_sequence_number()

    # update the dataframe display
    df = get_data(jsc.get_id(), jsc.get_sequence_number(), name='df_display', columns=columns)
    jsc['#df_display'].html = df.to_string()

    # update the charts
    for chart_name in ['chart_sample_hbar', 'chart_sample_line', 'chart_sample_pie', 'chart_sample_table', 'chart_sample_vbar',
                       'chart_sample_histogram', 'chart_histogram_table']:
        df = get_data(jsc.get_id(), jsc.get_sequence_number(), name=chart_name)
        jsc.update_chart(chart_name, df)


def btn_refresh_charts_with_cached_data_clicked(jsc):
    """ refresh charts with cached data, reuse the same sequence number """
    # update the dataframe display
    df = get_data(jsc.get_id(), jsc.get_sequence_number(), name='df_display')
    jsc['#df_display'].html = df.to_string()

    # update the charts
    for chart_name in ['chart_sample_hbar', 'chart_sample_line', 'chart_sample_pie', 'chart_sample_table', 'chart_sample_vbar',
                       'chart_sample_histogram', 'chart_histogram_table']:
        df = get_data(jsc.get_id(), jsc.get_sequence_number(), name=chart_name)
        jsc.update_chart(chart_name, df)


def ready(jsc, *args):
    """ called when a webpage creates a new connection the first time on load """
    # sequence number is still zero from initial loading so this data will stay in sync
    df = get_data(jsc.get_id(), jsc.get_sequence_number(), name='df_display')
    jsc['#df_display'].html = df.to_string()


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

