""" Plugin for Bokeh Applications """

# --------------------------------------------------
#    Imports
# --------------------------------------------------
import time
import pandas as pd
import bokeh.embed
import bokeh.models
import bokeh.plotting
from bokeh.plotting import curdoc


# --------------------------------------------------
#    Plugin
# --------------------------------------------------
class pluginBokeh:
    """ plugin for bokeh application """

    # --------------------------------------------------
    #    Constructor and Plugin Registration
    # --------------------------------------------------
    def __init__(self, get_data_handler=None):
        """ init """
        self._get_data_handler = get_data_handler
        self._kwargs = {
            'global_template_vars': {'create_chart': self._create_chart}
            }
        self.jsc_exposed_funcs = {'update_chart': self._update_chart}

    def register(self, kwargs):
        """ callback to register this plugin with the framework """
        # merge the dictionaries
        d = kwargs.get('global_template_vars', {})
        d.update(self._kwargs['global_template_vars'])
        self._kwargs['global_template_vars'] = d
        kwargs.update(self._kwargs)

    # --------------------------------------------------
    #    Private Functions
    # --------------------------------------------------
    @classmethod
    def _configure_color_palette(cls, df, user_palette=None):
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
        for c in df.columns:
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

    @classmethod
    def _extract_targetclass_kwargs(cls, targetclass, kwargs, delete=False):
        """ extract kwargs which match attibutes available on the target class

            Args:
                targetclass - class to check for attributes on
                kwargs - kwargs dictionary
                delete - if True, will remove matched items from kwargs

            Returns:
                dictionary of matched key values
        """
        params = {}
        for k in dir(targetclass):
            if (not k.startswith('_')) and (k in kwargs):
                params[k] = kwargs[k]
                if delete:
                    del kwargs[k]
        return params

    @classmethod
    def _prep_for_chart(cls, **kwargs):
        """ perform common preprocessing before creating a chart

            Kwargs:
                df - dataframe containing the data for the chart
                title - title of the figure, shorthand for __figure__title
                user_palette - palette for glyphs in the chart

            Returns:
                dictionary of processed variables necessary for chart generation
                    palette - generate color palette for the chart
                    cds - ColumnDataSource for the chart
        """
        # fix kwargs
        kwargs['title'] = kwargs.get('title', '')
        kwargs['user_palette'] = kwargs.get('user_palette', None)
        kwargs['name'] = kwargs.get('name', str(time.time()))

        # init the prepped values
        pv = {}

        # fix df
        df = kwargs.get('df', None)
        if df is None:
            df = pd.DataFrame()
        if df.empty:
            df = pd.DataFrame(data=[[0]], columns=['Blank'])

        # setup X axis index in the dataframe
        if 'X' in df.columns:
            df = df.set_index('X')
        else:
            df.index.name = 'X'
        pv['df'] = df

        # generate the palette
        pv['palette'] = cls._configure_color_palette(pv['df'], kwargs.get('user_palette', None))

        # create the column data source for bokeh
        pv['cds'] = bokeh.models.ColumnDataSource(bokeh.models.ColumnDataSource.from_df(pv['df']))

        # success!
        return pv

    @classmethod
    def _promote_kwargs_prefix(cls, prefixes, kwargs):
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


    # --------------------------------------------------
    #    Chart Creation Functions
    # --------------------------------------------------
    @classmethod
    def _create_hbar_chart(cls, data=None, **kwargs):
        """
            Create a horizontal bar chart
        """
        pass

    @classmethod
    def _create_line_chart(cls, **kwargs):
        """
            Create a line chart
        """
        # prep for the chart
        pv = cls._prep_for_chart(**kwargs)

        # create the figure
        figure_kwargs = cls._extract_targetclass_kwargs(bokeh.plotting.figure, kwargs, delete=True)
        figure_kwargs.update(cls._promote_kwargs_prefix(['__figure__'], figure_kwargs))
        p = bokeh.plotting.figure(**figure_kwargs)

        # create the lines
        for i, c in enumerate(pv['df'].columns):
            line_kwargs = dict(source=pv['cds'], x='X', y=c, color=pv['palette'][i], legend_label=c)
            line_kwargs.update(cls._promote_kwargs_prefix(['__line__', f'__line_{i}__'], kwargs))
            p.line(**line_kwargs)

        # add to the current document
        curdoc().add_root(p)

        # success!
        script, div = bokeh.embed.components(p)
        return script, div

    @classmethod
    def _create_vbar_chart(cls, data=None, **kwargs):
        pass

    def _create_chart(self, chart_type, **kwargs):
        if hasattr(self, f'_create_{chart_type}_chart'):
            if self._get_data_handler:
                if 'df' not in kwargs:
                    kwargs['__creation'] = True
                    kwargs['df'] = self._get_data_handler(**kwargs)

            script, div = getattr(self, f'_create_{chart_type}_chart')(**kwargs)
            return script + div
        else:
            raise Exception(f'No chart type of "{chart_type}" is available')

    @classmethod
    def _update_chart(cls, jsc, chart_name, df):
        pv = cls._prep_for_chart(df = df)
        cds_id = curdoc().get_model_by_name(chart_name).renderers[0].data_source.id
        new_val = str(pv['df'].reset_index().to_dict(orient='list'))
        js = f"""Bokeh.documents[0].get_model_by_id('{cds_id}').data = {new_val}"""
        jsc.eval_js_code(js)