import pandas as pd
from .bokehPlugin_util import promote_kwargs_prefix, prepare_for_chart_update_js, configure_color_palette, post_process_figure

def create_chart_df(pv):
    """
           counts  bin_text
<55%         79.0      79.0
55%-65%      72.0      72.0
65%-75%      25.0      25.0
75%-85%      74.0      74.0
85%-95%      52.0      52.0
95%-105%     13.0      13.0
105%-115%    26.0      26.0
115%-125%    43.0      43.0
125%-135%    63.0      63.0
135%-145%    27.0      27.0
145%-155%    50.0      50.0
>155%        79.0      79.0    
    """

    # init, grab the first color off the palette using a fake dataframe
#    data = {}
    palette = configure_color_palette(pd.DataFrame(index=[0], columns=['A']))

    # convert
    df = pv['df'].copy()
    df.index.name = 'factors'
    df = df.reset_index()
    df['fill_color'] = palette[0]
    df['line_color'] = palette[0]
    if not df.empty:
        df['counts_text'] = df['counts']
        df['counts2'] = df['counts'] * 1.2
        
    return df.reset_index()

def create_chart_js(target_div_id, pv, **kwargs):
    """ Create the javascript to create a line chart """
    pv['figure_kwargs']['x_range'] = []
    js = f"""
        var plt = Bokeh.Plotting;
        var f = new plt.Figure({pv['figure_kwargs']});
        """
    js += post_process_figure(**kwargs)
    js += update_chart_js(pv, **kwargs)
    js += f"plt.show(f, '#{target_div_id}');"
    return js

def update_chart_js(pv, chart_name=None, **kwargs):
    df = create_chart_df(pv)
    
    js = prepare_for_chart_update_js(chart_name, df)

    js += f"""
        f.x_range.factors = {list(df['factors'])};
        f.x_range.range_padding = 0.05;
        
        if (f.tags.length > 0) {{
            f.remove_layout(f.tags[0]);
            f.tags.pop();
        }}        
    """
    
    if not df.empty:
        js += f"""
        f.y_range = new Bokeh.Range1d({{start:0, end: {int(df['counts'].max() * 1.1)} }});
        """


    kwd = {}
    kwd['source'] = 'cds'
    kwd['x'] = "{field: 'factors'}"
    kwd['top'] = "{field: 'counts'}"
    kwd['width'] = 0.95
    kwd.update(promote_kwargs_prefix(['__histogram__'], kwargs))
    kwd['fill_color'] = "'white'"
    kwd['line_color'] = "'white'"
    kwd['top'] = "{field: 'counts2'}"
    kwds = ', '.join([f"'{k}': {v}" for k, v in kwd.items()])
    js += f"""
        // add the vbar    
        var vbo = f.vbar({{ {kwds} }});
    """
    kwd['top'] = "{field: 'counts'}"
    kwd['fill_color'] = "{field: 'fill_color'}"
    kwd['line_color'] = "{field: 'line_color'}"
    kwd.update(promote_kwargs_prefix(['__histogram__'], kwargs))
    kwds = ', '.join([f"'{k}': {v}" for k, v in kwd.items()])
    js += f"""
        // add the vbar    
        var vbo = f.vbar({{ {kwds} }});
        
        var lso = new Bokeh.LabelSet({{source: cds, x: {{field: 'factors'}}, y: {{field: 'counts'}}, text: {{field: 'bin_text'}}, level: 'glyph', 'text_align': 'center', y_offset: 5}})
        f.add_layout(lso);
        f.tags.push(lso);
        
        cds2 = cds;
        
    """
    return js
