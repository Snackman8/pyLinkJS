# bokeh horizontal bar chart generation code

# --------------------------------------------------
#    Imports
# --------------------------------------------------
import bokeh.models
from .bokehPlugin_util import post_process_figure, promote_kwargs_prefix, reset_figure


# --------------------------------------------------
#    Functions
# --------------------------------------------------
def create_chart_factors_cds(pv, flip_factors):
    """ create a set of factors and the corresponding ColumnDataSource
    
        Input DataFrame
        
            Columns are the labels for the bars inside the categories
            Index are the outer categories
        
                A   B   C
            X            
            0  25  13   8
            1  53  64  52
            2   0  15  80
    
        Args:
            pv - see create_chart_js documentation for pv documentation
            flip_factors - if True, reverse the order of the produced factors
    
        Returns:
            factors built up from the dataframe.  i.e. [(0, A), (0, B), (0,C), (1, A) ...]
            ColumnDataSource with the data rearranged so there is one data point per factor
                {'factors': [('0', 'A'), ('0', 'B'), ('0', 'C') ...],
                 'counts': [51, 43, 79 ...],
                 'line_color': ['#1f77b4', '#ff7f0e', '#2ca02c' ...],
                 'fill_color': ['#1f77b4', '#ff7f0e', '#2ca02c' ...]}
    """
    if pv['df'].empty:
        return [], bokeh.models.ColumnDataSource()

    # init
    data = {}

    # convert
    df = pv['df'].copy()
    df.index = df.index.map(str)

    # build the factors
    data['factors'] = [(x, c) for x in df.index for c in df.columns]
    if flip_factors:
        data['factors'] = data['factors'][::-1]

    # build the data
    counts = []
    fill_color = []
    line_color = []
    for i, f in enumerate(data['factors']):
        idx = f[0]
        c = f[1]
        counts.append(df.loc[idx, c])
        nc = len(df.columns)
        if flip_factors:
            fill_color.append(pv['palette'][nc - 1 - (i % nc)])
            line_color.append(pv['palette'][nc - 1 - (i % nc)])
        else:
            fill_color.append(pv['palette'][i % nc])
            line_color.append(pv['palette'][i % nc])

    if len(df.columns) == 1:
        data['factors'] = [x[0] for x in data['factors']]

    data['cds'] = bokeh.models.ColumnDataSource({'factors': data['factors'], 'counts': counts,
                                                 'line_color': line_color, 'fill_color': fill_color})

    # success!
    return data['factors'], data['cds']


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
    pv['figure_kwargs']['y_range'] = []
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
    
        Args:
            pv - see create_chart_js documentation for pv documentation

        Returns:
            javascript to update the chart with new data
    """    
    factors, cds = create_chart_factors_cds(pv, flip_factors=pv['kwargs'].get('flip_factors', False))
    df = cds.to_df()
    
    js = reset_figure(df, pv['figure_kwargs']['name'])

    # rebuilt the y_range factors
    factors_str = [[x[0], x[1]] for x in factors]
    js += f"""f.y_range.factors = {factors_str};"""

    kwd = {}
    kwd['source'] = 'cds'
    kwd['y'] = "{field: 'factors'}"
    kwd['right'] = "{field: 'counts'}"
    kwd['fill_color'] = "{field: 'fill_color'}"
    kwd['line_color'] = "{field: 'line_color'}"
    kwd['height'] = 0.8
    kwd.update(promote_kwargs_prefix(['__hbar__'], pv['kwargs']))
    kwds = ', '.join([f"'{k}': {v}" for k, v in kwd.items()])
    js += f"""
        // add the hbar    
        var hbo = f.hbar({{ {kwds} }});
    """
    return js
