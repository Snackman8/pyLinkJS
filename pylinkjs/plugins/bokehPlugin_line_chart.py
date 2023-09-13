import json
from .bokehPlugin_util import promote_kwargs_prefix

"""
                A   B   C
            X            
            0  21   3  24
            1  60  24  64
            2  72  68  13
"""

def create_chart_js(target_div_id, pv, **kwargs):
    """ Create the javascript to create a line chart """
    js = f"""
        var plt = Bokeh.Plotting;
        var f = new plt.Figure({pv['figure_kwargs']});
        """        
    js += update_chart_js(pv, **kwargs)
    js += f"plt.show(f, '#{target_div_id}');"
    
    return js

def update_chart_js(pv, chart_name=None, **kwargs):
    cds_data_json = json.dumps(pv['df'].reset_index().to_dict(orient='list'))
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
            f.legend.items.pop();
        }
        f.legend.change.emit();
    """                

    for i, c in enumerate(pv['df'].columns):
        kwd = {}
        kwd['source'] = 'cds'
        kwd['x'] = "{field: 'X'}"
        kwd['y'] = f"{{field: '{c}'}}"
        kwd['color'] = f"'{pv['palette'][i]}'"
        kwd.update(promote_kwargs_prefix(['__line__', f'__line_{i}__'], kwargs))
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
