import bokeh.palettes
import json



def configure_color_palette(df, user_palette=None):
    """ configure a list of colors to rotate through on the charts

        Args:
            df - dataframe containing data
            user_palette - a user supplied 2D palette, default is bokeh Category10

        Returns:
            a normalized palette large enough to color the data
    """
    # setup the base palette
    if user_palette is None:
        user_palette = bokeh.palettes.Category10

    # calculate colors needed
    colors_needed = 0
    for c in df.columns.map(str):
        if not c.startswith('_'):
            colors_needed = colors_needed + 1

    # calculate best color range in palette
    cr_min = sorted(user_palette.keys())[0]
    cr_max = sorted(user_palette.keys())[-1]
    color_range = min(cr_max, max(cr_min, colors_needed))

    # calculate number of colors available in that color range
    cr_colors_available = len(user_palette[color_range])

    # generate palette
    palette = []
    for i in range(0, colors_needed):
        palette.append(user_palette[color_range][i % cr_colors_available])

    # success!
    return palette


def promote_kwargs_prefix(prefixes, kwargs):
    """ return keyword args that start with a prefix.  the returned dictionary will have the prefix strippped

        Args:
            prefixes - list of prefixes to match for, i.e. '__figure__', '__figure(0)__'
            kwargs - keyword args dictionary

        Returns:
            dictionary containing the found keyword args but with the prefix stripped off
    """
    promoted = {}
    for k in kwargs.keys():
        for p in prefixes[::-1]:
            if k.startswith(p):
                promoted[k[len(p):]] = kwargs[k]
                break
    return promoted


def post_process_figure(**kwargs):
    js = ''
    if not kwargs.get('toolbar_visible', True):
        js += """f.toolbar.visible = false; \n""" 
    return js


def prepare_for_chart_update_js(chart_name, df):
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
    
    return js              
    