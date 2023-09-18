""" functions to create a line chart for the Bokeh PyLinkeJS plugin """

# --------------------------------------------------
#    Imports
# --------------------------------------------------
from .bokehPlugin_util import post_process_figure, promote_kwargs_prefix, reset_figure


# --------------------------------------------------
#    Functions
# --------------------------------------------------
def create_chart_js(pv):
    """ Create the javascript to create a chart
    
        Args:
            target_div_id - id of the div which will contain the chart
            pv - dict of prepared values
                    'df' - dataframe passed in by user
                    'div_id' - id of the div to target
                    'figure_kwargs' - keyword args passed in that affect figure creation
                        'name' - name of the chart
                        (see bokeh Figure documentation for full list)
                    'kwargs' - keyword arguments passed in during initial chart creation
                        (keyword args prefaced with __wedge__ will be passed in for wedge creation.
                         see Bokeh wedge documentation for full list of available keywords)
                    'palette' - color palette to use for chart rendering

        Returns:
            javascript to create the initial chart
    """
    js = f"""
        var plt = Bokeh.Plotting;
        var f = new plt.Figure({pv['figure_kwargs']});
        """
    js += post_process_figure(**pv['kwargs'])
    js += update_chart_js(pv)
    js += f"""plt.show(f, '#{pv["div_id"]}');"""
    
    return js


def update_chart_js(pv):
    """ update the chart with new data

            Dataframe Input

                - A, B, C are the names of the lines
                - 0, 1, 2 is the X axis
                - cell values are the Y values

                    A   B   C
                0  58   5  51
                1  51  85  83
                2   5  70  95

        Args:
            pv - see create_chart_js documentation for pv documentation

        Returns:
            javascript to update the chart with new data
    """    
    # reset the figure
    js = reset_figure(pv['df'], pv['figure_kwargs']['name'])

    # add the new glyphs
    for i, c in enumerate(pv['df'].columns):
        kwd = {}
        kwd['source'] = 'cds'
        kwd['x'] = "{field: 'X'}"
        kwd['y'] = f"{{field: '{c}'}}"
        kwd['color'] = f"'{pv['palette'][i]}'"
        kwd.update(promote_kwargs_prefix(['__line__', f'__line_{i}__'], pv['kwargs']))
        kwds = ', '.join([f"'{k}': {v}" for k, v in kwd.items()])

        js += f"""
            // add the line    
            var lo = f.line({{ {kwds} }});
            
            // add the legend item
            var lio = new Bokeh.LegendItem({{label: '{c}'}});
            lio.renderers.push(lo);
            f.legend.items.push(lio);
            f.legend.change.emit();
        """
    return js
