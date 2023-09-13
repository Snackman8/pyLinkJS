import json
import bokeh.embed
import bokeh.models
from .bokehPlugin_util import promote_kwargs_prefix


def create_chart_js(target_div_id, pv, **kwargs):    
    """ Create the javascript to create a chart """
    return ''


def update_chart_js(pv, chart_name=None, **kwargs):
    div_id = f"div_{kwargs['name']}"
    df = pv['df']
    cds = bokeh.models.ColumnDataSource(df)
    
    # plot the table
    table_kwargs = pv['figure_kwargs']
    table_kwargs.update({'source': cds})
    table_kwargs.update(promote_kwargs_prefix(['__table__'], kwargs))
    table_kwargs['columns'] = [bokeh.models.widgets.TableColumn(field=Ci, title=Ci) for Ci in df.columns]
    del table_kwargs['title']

    # # create the figure
    p = bokeh.models.widgets.DataTable(**table_kwargs)

    j = json.dumps(bokeh.embed.json_item(p, div_id))
    js = f"""
        $("#{div_id}").empty();
        window.Bokeh.embed.embed_item(JSON.parse('{j}'), '{div_id}');
        """
    return js
