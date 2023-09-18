from .bokehPlugin_util import post_process_figure, promote_kwargs_prefix, reset_figure

"""
                A   B   C
            X            
            0  21   3  24
            1  60  24  64
            2  72  68  13
"""

#def create_chart_js(target_div_id, pv, **kwargs):
def create_chart_js(pv):
    """ Create the javascript to create a line chart """
    js = f"""
        var plt = Bokeh.Plotting;
        var f = new plt.Figure({pv['figure_kwargs']});
        """
    js += post_process_figure(**pv['kwargs'])
    js += update_chart_js(pv)
    js += f"""plt.show(f, '#{pv["div_id"]}');"""
    
    return js

def update_chart_js(pv):
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
