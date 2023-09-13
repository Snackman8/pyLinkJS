import json
import math
import bokeh.embed
import bokeh.models
from .bokehPlugin_util import promote_kwargs_prefix

# def create_chart_df(pv):
#     """
# #                 A   B   C
# #             0  21   3  24
#     """
#     if pv['df'].empty:
#         return pv['df']
#
#     # recompute pv since a pie chart only works on the first row
#     df = pv['df'].head(1).reset_index().T[1:]
#     df = df.rename(columns={df.columns[0]: 'value'})
#     df['angle'] = df['value'] / df['value'].sum() * 2 * math.pi
#     df['color'] = pv['palette']
#     df["text_value"] = df['value'].astype(str)
# #    df["text_value"] = df["text_value"].str.pad(12, side = "left")
#     df['end_angle'] = df['angle'].cumsum()
#     df['start_angle'] = df['end_angle'].shift(1).fillna(0)
#     df['text_angle'] = (df['start_angle'] + df['end_angle']) / 2
#     df.index.name = 'legend'
#     print(df.to_string())
#     return df


def create_chart_js(target_div_id, pv, **kwargs):    
    """ Create the javascript to create a chart """
    
    cds = bokeh.models.ColumnDataSource(pv['df'])

    
    # plot the table
    table_kwargs = pv['figure_kwargs']
    table_kwargs.update({'source': cds})
    table_kwargs.update(promote_kwargs_prefix(['__table__'], kwargs))
    table_kwargs['columns'] = [bokeh.models.widgets.TableColumn(field=Ci, title=Ci) for Ci in pv['df'].columns]
    del table_kwargs['title']

    # # create the figure
    p = bokeh.models.widgets.DataTable(**table_kwargs)
    
    script, div = bokeh.embed.components(p)
    return '</script>' + script + div + '<script>'
    
#
# #        p = DataTable(columns=columns, source=bokeh.models.ColumnDataSource(pv['df']
#
#
#
#         # create the data
#         data = cls._create_line_chart_data(pv)
#
#         # plot the table
#         table_kwargs = pv['figure_kwargs']
#         table_kwargs.update({'source': data['cds']})
#         table_kwargs.update(cls._promote_kwargs_prefix(['__table__'], kwargs))
#         table_kwargs['columns'] = [bokeh.models.widgets.TableColumn(field=Ci, title=Ci) for Ci in pv['df'].columns]
#         del table_kwargs['title']
#
#         # # create the figure
#         p = bokeh.models.widgets.DataTable(**table_kwargs)
#
#
#
#     js = f"""
#         var plt = Bokeh.Plotting;
#         var f = new plt.Figure({pv['figure_kwargs']});
#         """        
#     js += update_chart_js(pv, **kwargs)
#     js += f"plt.show(f, '#{target_div_id}');"
#
#     return js


def update_chart_js(pv, chart_name=None, **kwargs):
    new_val = pv['df'].to_dict(orient='list')

    js = ''
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

    
    js += f"""Bokeh.documents[{doc_index}].get_model_by_id('{cds_id}').data = {json.dumps(new_val)};"""
    
    df = pv['df']
    return ''
    # df = create_chart_df(pv)
    #
    # cds_data_json = json.dumps(df.reset_index().to_dict(orient='list'))
    # print(cds_data_json)
    # js = f"""
    #     var plt = Bokeh.Plotting;
    #     var data_json = JSON.parse('{cds_data_json}');
    #     var cds = new Bokeh.ColumnDataSource({{'data': data_json}});
    # """
    #
    # if chart_name is not None:
    #     js += f"""
    #     var f;
    #
    #     for (let i = 0; i < Bokeh.documents.length; i++) {{
    #         f = Bokeh.documents[i].get_model_by_name('{chart_name}');
    #         if (f != null) {{
    #             break;
    #         }}
    #     }}
    # """ 
    #
    # # remove the old glyphs
    # js += """
    #     for (let i = f.renderers.length - 1; i >= 0; i--) {
    #         f.renderers[i].visible = false;
    #         f.renderers.pop();
    #         f.legend.items.pop();
    #         f.x_range.renderers.pop();
    #     }
    #     f.legend.change.emit();
    # """
    #
    # # add pie wedges    
    # for i, c in enumerate(pv['df'].columns):
    #     kwd = {}
    #     kwd['source'] = 'cds'
    #     kwd['x'] = 0
    #     kwd['y'] = 0
    #     kwd['radius'] = 2
    #     kwd['radius_units'] = "'data'"
    #     kwd['color'] = f"'{pv['palette'][i]}'"
    #     kwd['start_angle'] = df.iloc[i]['start_angle']
    #     kwd['end_angle'] = df.iloc[i]['end_angle']
    #     kwd['start_angle_units'] = "'rad'"
    #     kwd['end_angle_units'] = "'rad'"
    #     kwd.update(promote_kwargs_prefix(['__wedge__', f'__wedge_{i}__'], kwargs))
    #     kwds = ', '.join([f"'{k}': {v}" for k, v in kwd.items()])
    #
    #     js += f"""
    #         // add the wedge    
    #         var wo = f.wedge({{ {kwds} }});
    #
    #         // add the legend item
    #         var lio = new Bokeh.LegendItem({{label: '{c}'}});
    #         lio.renderers.push(wo);
    #         f.legend.items.push(lio);
    #         f.legend.change.emit();
    #
    #         // make sure to push the renderer to the autoranger
    #         f.x_range.renderers.push(wo);
    #     """
    #
    # # add overlay text    
    # for i, c in enumerate(pv['df'].columns):
    #     kwd = {}
    #     kwd['x'] = 0 + math.cos(df.iloc[i]['text_angle']) * 0.75
    #     kwd['y'] = 0 + math.sin(df.iloc[i]['text_angle']) * 0.75
    #     kwd['text_color'] = f"'white'"
    #     kwd['text'] =  f"'{df.iloc[i]['text_value']}'"
    #     kwds = ', '.join([f"'{k}': {v}" for k, v in kwd.items()])
    #
    #     js += f"""
    #         // add the text
    #         f.text({{ {kwds} }});
    #         """
    #
    # print(js)
    # return js
