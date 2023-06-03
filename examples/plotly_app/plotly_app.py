#--------------------------------------------------
#   Imports
#--------------------------------------------------
import json
import logging
import numpy as np
import pandas as pd
from pylinkjs.PyLinkJS import run_pylinkjs_app
from pylinkjs.plugins.bokehPlugin import pluginBokeh
import plotly.graph_objects as go
import plotly.io as pio


# --------------------------------------------------
#    Plotly Helper Functions
# --------------------------------------------------
def plotly_data_surface_y(x_vals, y, z_bottom, z_top, color='blue', opacity=0.2):
    """ Create vertical planes """
    x = x_vals
    y = [y] * len(x)
    z = [z_bottom, z_top]
    colorscale = [[0, color], [1, color]]
    plane = go.Surface(x=x, y=y, z=z, colorscale=colorscale, opacity=opacity, hoverinfo='skip', hovertemplate=None, showscale=False)
    return plane

def plotly_data_surface_z(x_vals, y_vals, z_vals, color='black', opacity=0.2):
    """ Create a horizontal ground plane
        data_surface_z([-5, 3, 9], [2, 4], [0, 0, 0, 1, 0, 0]) """
    x = x_vals
    y = y_vals
    z = np.array(z_vals).reshape(len(y), len(x))
    colorscale = [[0, color], [1, color]]
    plane = go.Surface(x=x, y=y, z=z, colorscale=colorscale, opacity=opacity, hoverinfo='skip', hovertemplate=None, showscale=False)
    return plane

def plotly_update_plot(jsc, plot_id, fig, config):
    js = f"""{{ var figtemp={pio.to_json(fig)}; last_plot = Plotly.newPlot("{plot_id}", figtemp['data'], figtemp['layout'], {json.dumps(config)}); }} """
    jsc.eval_js_code(js);


# --------------------------------------------------
#    Functions
# --------------------------------------------------
def refresh_initiative_plot(jsc, df):
    # get the initiative data
    palette = pluginBokeh._configure_color_palette(df)
    
    # transform the data for plotly
    data = []
    i = 0
    for name in df.columns:
        x = list(df.index)
        z = list(df[name])
        data.append(plotly_data_surface_y(x, name, [0] * len(x), z, color=palette[i], opacity=0.3))
        i = i + 1

    # build the layout
    layout = dict(
        font=dict(size=18),
        showlegend=False,
        margin=dict(l=0, r=0, t=0, b=0),
        scene=dict(
            hovermode=False,
            xaxis=dict(title='', showspikes=False),
            yaxis=dict(title='', showspikes=False),
            zaxis=dict(title='', showspikes=False),
            camera=dict(
                eye=dict(x=-4, y=-1.7, z=3)
            )
        )
    )

    # build the config
    config = {'displayModeBar': False,
              'responsive': True}
    
    # craete the figure and update the plot
    fig = dict(data=data, layout=layout)    
    plotly_update_plot(jsc, 'plotly_isochart', fig, config)


def refresh_page(jsc):
    # get the latest data
    df = get_data()
    
    # get the checked boxes    
    js = """$('input[type=checkbox]').map(function() {if ($(this).is(':checked')) return $(this).attr('value')}).toArray();"""
    checked_columns = jsc.eval_js_code(js);
    for c in df.columns:
        if c not in checked_columns:
            df[c] = 0
    print(checked_columns)
    
    # refresh the plotly plot
    refresh_initiative_plot(jsc, df )

    # refresh the bokeh chart    
    jsc.update_chart('chart_sandchart', df)


# --------------------------------------------------
#    Event Handlers
# --------------------------------------------------
def checkbox_clicked(jsc, name):
    refresh_page(jsc)


def ready(jsc, *args):
    """ called when a webpage creates a new connection the first time on load """
    # generate the initiatives
    df = get_data()

    html = ''
    for n in df.columns:
        html += f"""<input type="checkbox" value="{n}" onclick="call_py('checkbox_clicked', '{n}');" checked>{n}<br>"""
    jsc['#checkboxes'].html = html
    
    refresh_page(jsc)


def get_data(**kwargs):
    """    
        name  aliqua  consectetur adipisicing  elit eiusmod  elit sed do eiusmod  et dolore magna  labore
        x                                                                                                
        2023       5                        4             3                    9                5       8
        2024       7                        4             3                    0                1       5
        2025       6                        2             3                   10                9       0
        2026       3                        2             6                    7                2       4
        2027       8                        2             0                    1                3      10    
    """
    df = pd.read_csv('test_data.csv').set_index('name').T
    df.index.name = 'X'
    return df
    

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
    run_pylinkjs_app(default_html='plotly_app.html',
                     port=port,
                     plugins=[bokeh_plugin])

if __name__ == '__main__':
    main()
