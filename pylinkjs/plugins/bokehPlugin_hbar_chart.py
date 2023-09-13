import json
import bokeh.models
from .bokehPlugin_util import promote_kwargs_prefix

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

def create_chart_js(target_div_id, pv, **kwargs):
    """ Create the javascript to create a line chart """
    pv['figure_kwargs']['y_range'] = []
    js = f"""
        var plt = Bokeh.Plotting;
        var f = new plt.Figure({pv['figure_kwargs']});
        """
    js += update_chart_js(pv, **kwargs)
    js += f"plt.show(f, '#{target_div_id}');"
    return js

def update_chart_js(pv, chart_name=None, **kwargs):
    factors, cds = create_chart_factors_cds(pv, flip_factors=kwargs.get('flip_factors', False))
    df = cds.to_df()
    cds_data_json = json.dumps(df.reset_index().to_dict(orient='list'))
    js = f"""
        var plt = Bokeh.Plotting;
        var data_json = JSON.parse('{cds_data_json}');
        var cds = new Bokeh.ColumnDataSource({{'data': data_json}});
    """
    
    if chart_name is not None:
        js += f"""
        var f;
        
        for (let i = 0; i < Bokeh.documents.length; i++) {{
            f = Bokeh.documents[i].get_model_by_name('{chart_name}');
            if (f != null) {{
                break;
            }}
        }}
    """ 
    
    # remove the old glyphs
    js += """
        for (let i = f.renderers.length - 1; i >= 0; i--) {
            f.renderers[i].visible = false;
            f.renderers.pop();
        }
    """                

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
    kwd.update(promote_kwargs_prefix(['__hbar__'], kwargs))
    kwds = ', '.join([f"'{k}': {v}" for k, v in kwd.items()])
    js += f"""
        // add the hbar    
        var hbo = f.hbar({{ {kwds} }});
    """
    return js
