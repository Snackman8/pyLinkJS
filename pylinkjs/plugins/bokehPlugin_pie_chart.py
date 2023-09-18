# bokeh pie chart generation code

# --------------------------------------------------
#    Imports
# --------------------------------------------------
import math
from .bokehPlugin_util import promote_kwargs_prefix, post_process_figure, reset_figure



 

# --------------------------------------------------
#    Functions
# --------------------------------------------------
def create_chart_df(pv):
    """ create dataframe for the chart from prepared values

        Input Dataframe
            Index is labels for pie chart segments
            "value" column is the value for the wedge (required)
            "text" column is the text to display in the wedge (optional)

                    A   B   C
            value  10  20  30
            text   1A  2B  3C

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
    # init
    df = pv['df'].T
    
    # a blank chart will pass in an empty dataframe
    if df.empty:
        return df

    # make first column value if value is not present
    if 'value' not in df.columns:
        df = df.rename(columns={df.columns[0]: 'value'})

    # fill in optional values
    if 'text' not in df.columns:
        df["text"] = df['value'].astype(str)

    # compute values necessary for rendering
    df['angle'] = df['value'] / df['value'].sum() * 2 * math.pi
    df['color'] = pv['palette']
    df['end_angle'] = df['angle'].cumsum()
    df['start_angle'] = df['end_angle'].shift(1).fillna(0)
    df['text_angle'] = (df['start_angle'] + df['end_angle']) / 2
    df.index.name = 'legend'
    return df


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
    # standard boilerplate
    js = f""" {{
              var plt = Bokeh.Plotting;
              var f = new plt.Figure({pv['figure_kwargs']}); \n"""
    js += post_process_figure(**pv['kwargs'])              
    js += update_chart_js(pv)
    js += f"""plt.show(f, '#{pv["div_id"]}'); \n"""

    # extra specific to this type of chart
    js += f"""f.grid.visible = false; \n"""
    js += f"""f.axis.visible = false; \n"""
    js += f"""f.x_range = new Bokeh.Range1d({{start: -1, end: 1}}); \n"""
    js += f"""f.y_range = new Bokeh.Range1d({{start: -1, end: 1}}); \n"""
    js += f"""}} \n"""
    return js


def update_chart_js(pv):
    """ update the chart with new data
    
        Args:
            pv - see create_chart_js documentation for pv documentation

        Returns:
            javascript to update the chart with new data
    """
    # convert the prepared values into a dataframe
    df = create_chart_df(pv)

    # reset the figure
    js = reset_figure(df, pv['figure_kwargs']['name'])

    # add pie wedges    
    for i, c in enumerate(df.index):
        kwd = {}
        kwd['source'] = 'cds'
        kwd['x'] = 0
        kwd['y'] = 0
        kwd['radius'] = 0.5
        kwd['radius_units'] = "'data'"
        # colors must be quoted string
        kwd['color'] = f"'{pv['palette'][i]}'"
        kwd['start_angle'] = df.iloc[i]['start_angle']
        kwd['end_angle'] = df.iloc[i]['end_angle']
        kwd['start_angle_units'] = "'rad'"
        kwd['end_angle_units'] = "'rad'"
        kwd.update(promote_kwargs_prefix(['__wedge__', f'__wedge_{i}__'], pv['kwargs']))
        kwds = ', '.join([f"'{k}': {v}" for k, v in kwd.items()])
                
        js += f""" // add the wedge    
                   var wo = f.wedge({{ {kwds} }});
            
                   // add the legend item
                   var lio = new Bokeh.LegendItem({{label: '{c}'}});
                   lio.renderers.push(wo);
                   f.legend.items.push(lio);
                   f.legend.change.emit();

                   // add the text
                   var ar =  (f.inner_height / f.inner_width);   
                   var tx = {kwd['radius'] * math.cos(df.iloc[i]['text_angle']) * 0.5};
                   var ty = {kwd['radius'] * math.sin(df.iloc[i]['text_angle']) * 0.5} / ar;
                   f2 = f;
                   f.text({{x: tx, y: ty, text: '{df.iloc[i]['text']}', text_align: 'center', text_baseline: 'middle', color: 'white'}}); \n"""

    return js
