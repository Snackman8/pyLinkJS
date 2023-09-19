# bokeh boxchart chart generation code

# --------------------------------------------------
#    Imports
# --------------------------------------------------
import pandas as pd
import bokeh.models
from .bokehPlugin_util import post_process_figure, reset_figure, configure_color_palette


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
    pv['figure_kwargs']['x_range'] = []
    js = f"""
        var plt = Bokeh.Plotting;
        var f = new plt.Figure({pv['figure_kwargs']});
        """
    js += post_process_figure(**pv['kwargs'])
    js += update_chart_js(pv)
    js += f"""plt.show(f, '#{pv["div_id"]}');"""
    return js


def update_chart_js(pv):
    """ update the chart with new data

        Args:
            pv - see create_chart_js documentation for pv documentation

        Returns:
            javascript to update the chart with new data
    """

    # init, grab the first color off the palette using a fake dataframe
    kwargs = {}
    if 'user_palette' in pv['kwargs']:
        kwargs['user_palette'] = pv['kwargs'] ['user_palette']
    palette = configure_color_palette(pd.DataFrame(index=[0], columns=['A', 'B', 'C']), **kwargs)

    df = pv['df']

    if df.empty:
        return ''


    d = {
        'factors': list(df.columns),
        'mean': df.mean().values,
        'upper': (df.mean() + df.std() * 3).values,
        'lower': (df.mean() - df.std() * 3).values,
        '25percentile': df.describe().loc['25%'].values,
        '75percentile': df.describe().loc['75%'].values
    }
    cds = bokeh.models.ColumnDataSource(d)
    df = cds.to_df()

    js = reset_figure(df, pv['figure_kwargs']['name'], no_legend=True)

    # rebuilt the y_range factors
    factors_str = d['factors']
    js += f"""f.x_range.factors = {factors_str};"""

    i = 0
    for _, r in df.iterrows():
        js += f"""
            f.line({{x: [{0.5 + i - 0.1}, {0.5 + i + 0.1}], y: [{r.lower}, {r.lower}], line_color: '{palette[0]}' }});
            f.line({{x: [{0.5 + i - 0.1}, {0.5 + i + 0.1}], y: [{r.upper}, {r.upper}], line_color: '{palette[0]}' }});
            f.line({{x: [{0.5 + i}, {0.5 + i}], y: [{r.upper}, {r.lower}], line_color: '{palette[0]}' }});
            f.quad({{ left: {0.5 + i - 0.2}, right: {0.5 + i + 0.2}, top: {r["mean"]}, bottom: {r["25percentile"]}, fill_color: '{palette[1]}' }});
            f.quad({{ left: {0.5 + i - 0.2}, right: {0.5 + i + 0.2}, top: {r["75percentile"]}, bottom: {r["mean"]}, fill_color: '{palette[2]}' }});
        """
        i = i + 1
    return js
