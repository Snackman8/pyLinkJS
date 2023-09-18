# bokeh table chart generation code

# --------------------------------------------------
#    Imports
# --------------------------------------------------
import json
import bokeh.embed
import bokeh.models
from .bokehPlugin_util import promote_kwargs_prefix


# --------------------------------------------------
#    Functions
# --------------------------------------------------
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
    # table creation is done all within update_chart_js
    return ''


def update_chart_js(pv):
    """ update the chart with new data
    
        Args:
            pv - see create_chart_js documentation for pv documentation

        Returns:
            javascript to update the chart with new data
    """
    df = pv['df']
    cds = bokeh.models.ColumnDataSource(df)
    
    # plot the table
    table_kwargs = pv['figure_kwargs']
    table_kwargs.update({'source': cds})
    table_kwargs.update(promote_kwargs_prefix(['__table__'], pv['kwargs']))
    table_kwargs['columns'] = [bokeh.models.widgets.TableColumn(field=Ci, title=Ci) for Ci in df.columns]
    
    # DataTable does not accept title parameter, so remove
    del table_kwargs['title']

    # # create the figure
    p = bokeh.models.widgets.DataTable(**table_kwargs)

    j = json.dumps(bokeh.embed.json_item(p, pv['div_id']))
    js = f"""
        $("#{pv['div_id']}").empty();
        window.Bokeh.embed.embed_item(JSON.parse('{j}'), '{pv['div_id']}');
        """
    print(js)
    return js
