import json
import math
from .bokehPlugin_util import promote_kwargs_prefix

def create_chart_df(pv):
    """
#                 A   B   C
#             0  21   3  24
    """
    if pv['df'].empty:
        return pv['df']

    # recompute pv since a pie chart only works on the first row
    df = pv['df'].head(1).reset_index().T[1:]
    df = df.rename(columns={df.columns[0]: 'value'})
    df['angle'] = df['value'] / df['value'].sum() * 2 * math.pi
    df['color'] = pv['palette']
    df["text_value"] = df['value'].astype(str)
    df["text_value"] = df["text_value"].str.pad(6, side = "left")
    df['end_angle'] = df['angle'].cumsum()
    df['start_angle'] = df['end_angle'].shift(1).fillna(0)
    df['text_angle'] = (df['start_angle'] + df['end_angle']) / 2
    df.index.name = 'legend'
    return df


def create_chart_js(target_div_id, pv, **kwargs):
    """ Create the javascript to create a chart """
    js = f"""
        var plt = Bokeh.Plotting;
        var f = new plt.Figure({pv['figure_kwargs']});
        f.grid.visible = false;
        f.axis.visible = false;
        """        
    js += update_chart_js(pv, **kwargs)
    js += f"plt.show(f, '#{target_div_id}');"
    
    return js


def update_chart_js(pv, chart_name=None, **kwargs):
    df = create_chart_df(pv)

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
            f.legend.items.pop();
            f.x_range.renderers.pop();
        }
        f.legend.change.emit();
    """

    js += """
        
        for (i = 0; i < f.tags.length; i++) {
            f.tags[i].visible = false;
            console.log('AAAA');
        }
/*        
        while (f.tags.length > 0) {{
            f.tags[0].visible = false;
            console.log('AAAA');
//            f.remove_layout(f.tags[0]);
  //          f.tags.pop();
        }}        
  */  
    """

    # add pie wedges    
    for i, c in enumerate(pv['df'].columns):
        kwd = {}
        kwd['source'] = 'cds'
        kwd['x'] = 0
        kwd['y'] = 0
        kwd['radius'] = 0.5
        kwd['radius_units'] = "'data'"
        kwd['color'] = f"'{pv['palette'][i]}'"
        kwd['start_angle'] = df.iloc[i]['start_angle']
        kwd['end_angle'] = df.iloc[i]['end_angle']
        kwd['start_angle_units'] = "'rad'"
        kwd['end_angle_units'] = "'rad'"
        kwd.update(promote_kwargs_prefix(['__wedge__', f'__wedge_{i}__'], kwargs))
        kwds = ', '.join([f"'{k}': {v}" for k, v in kwd.items()])
#        radius = kwd['radius']
        js += f"""
            // add the wedge    
            var wo = f.wedge({{ {kwds} }});
            
            // add the legend item
            var lio = new Bokeh.LegendItem({{label: '{c}'}});
            lio.renderers.push(wo);
            f.legend.items.push(lio);
            f.legend.change.emit();
            
            // make sure to push the renderer to the autoranger
            f.x_range.renderers.push(wo);
/*
            var lso = new Bokeh.LabelSet({{source: cds, x: 0, y: 0, text: {{field: 'text_value'}}, level: 'glyph', 'text_color': 'white', angle: {{field: 'text_angle'}}}})
            f.add_layout(lso);
            f.tags.push(lso);

            pie_lso = lso;
*/                        
        """

        # labels = bokeh.models.LabelSet(x=0, y=1, text='text_value',
        #                   angle=bokeh.transform.cumsum('text_angle', include_zero=True), source=data['cds'], text_color='white')
        # p.add_layout(labels)


    # # add overlay text    
    # for i, c in enumerate(pv['df'].columns):
    #     kwd = {}
    #     kwd['x'] = 0 + math.cos(df.iloc[i]['text_angle']) * radius / 2
    #     kwd['y'] = 0 + math.sin(df.iloc[i]['text_angle']) * radius / 2
    #     kwd['text_color'] = f"'black'"
    #     kwd['text'] =  f"'{df.iloc[i]['text_value']}'"
    #     kwds = ', '.join([f"'{k}': {v}" for k, v in kwd.items()])
    #
    #     js += f"""
    #         // add the text
    #         f.text({{ {kwds} }});
    #         """
        
    return js
