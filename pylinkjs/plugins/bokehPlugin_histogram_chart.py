# bokeh histogram chart generation code

# --------------------------------------------------
#    Imports
# --------------------------------------------------
import pandas as pd
from .bokehPlugin_util import promote_kwargs_prefix, configure_color_palette, post_process_figure, reset_figure


# --------------------------------------------------
#    Functions
# --------------------------------------------------
def create_chart_df(pv):
    """ create dataframe for the chart from prepared values

        Input Dataframe
            Index is labels for histogram bins
            counts column contains the counts for each bin
            bin_text column contains the text to display above each bin

               counts bin_text
            A      91      A A
            B      60      B B
            C      99      C C

        Args:
            pv - dict of prepared values
                    'df' - dataframe passed in by user

        Returns:
            dataframe specific to this type of chart

                    value text     angle    color  end_angle  start_angle  text_angle
            legend                                                                   
            A          10   1A  1.047198  #1f77b4   1.047198     0.000000    0.523599
            B          20   2B  2.094395  #ff7f0e   3.141593     1.047198    2.094395
            C          30   3C  3.141593  #2ca02c   6.283185     3.141593    4.712389            
    """
    # init, grab the first color off the palette using a fake dataframe
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
    pv['figure_kwargs']['x_range'] = []
    js = f"""
        var plt = Bokeh.Plotting;
        var f = new plt.Figure({pv['figure_kwargs']});
        """
    js += post_process_figure(**pv['kwargs'])
    js += update_chart_js(pv)
    js += f"plt.show(f, '#{pv['div_id']}');"
    return js

def update_chart_js(pv):
    """ update the chart with new data
    
        Args:
            pv - see create_chart_js documentation for pv documentation

        Returns:
            javascript to update the chart with new data
    """
    df = create_chart_df(pv)
    
    js = reset_figure(df, pv['figure_kwargs']['name'])

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
    kwd.update(promote_kwargs_prefix(['__histogram__'], pv['kwargs']))
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
    kwd.update(promote_kwargs_prefix(['__histogram__'], pv['kwargs']))
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
