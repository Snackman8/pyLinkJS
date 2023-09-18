import bokeh.models
from .bokehPlugin_util import post_process_figure, promote_kwargs_prefix, reset_figure

def create_chart_factors_cds(pv, flip_factors):
    """
    A   B   C
X            
0  25  13   8
1  53  64  52
2   0  15  80
3  91  31   3
4  14  54  19
5  30  31  40
6  20   4  89
7  16  86  10
8  18  80  97
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
    """ Create the javascript to create a line chart """
    pv['figure_kwargs']['x_range'] = []
    js = f"""
        var plt = Bokeh.Plotting;
        var f = new plt.Figure({pv['figure_kwargs']});
        """
    js += post_process_figure(**pv['kwargs'])
    js += update_chart_js(pv)
    js += f"""plt.show(f, '#{pv["div_id"]}');"""
    return js

def update_chart_js(pv):
    factors, cds = create_chart_factors_cds(pv, flip_factors=pv['kwargs'].get('flip_factors', False))
    df = cds.to_df()
    
    js = reset_figure(df, pv['figure_kwargs']['name'])

    # rebuilt the y_range factors
    factors_str = [[x[0], x[1]] for x in factors]
    js += f"""f.x_range.factors = {factors_str};"""

    kwd = {}
    kwd['source'] = 'cds'
    kwd['x'] = "{field: 'factors'}"
    kwd['top'] = "{field: 'counts'}"
    kwd['fill_color'] = "{field: 'fill_color'}"
    kwd['line_color'] = "{field: 'line_color'}"
    kwd['width'] = 0.8
    kwd.update(promote_kwargs_prefix(['__vbar__'], pv['kwargs']))
    kwds = ', '.join([f"'{k}': {v}" for k, v in kwd.items()])
    js += f"""
        // add the vbar    
        var vbo = f.vbar({{ {kwds} }});
    """
    return js
