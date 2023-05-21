""" Plugin for Bokeh Applications """

# --------------------------------------------------
#    Imports
# --------------------------------------------------
import json
import math
import time
import pandas as pd
import bokeh.embed
import bokeh.models.widgets
import bokeh.plotting
import bokeh.transform


# --------------------------------------------------
#    Plugin
# --------------------------------------------------
class pluginBokeh:
    """ plugin for bokeh application """
    # --------------------------------------------------
    #    Class Variables
    # --------------------------------------------------
    BOKEH_CONTEXT = {}

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
    #    Event Handlers
    # --------------------------------------------------
    @classmethod
    def on_context_close(cls, jsc):
        # delete the bokeh document associated with js clients that are closing
        del cls.BOKEH_CONTEXT[jsc._jsc_id]

    @classmethod
    def on_context_open(cls, jsc):
        # create a new bokeh document if needed for this js client.  this may have been created
        # during page template rendering
        if jsc._jsc_id not in cls.BOKEH_CONTEXT:
            cls.BOKEH_CONTEXT[jsc._jsc_id] = {}
        if 'Document' not in cls.BOKEH_CONTEXT[jsc._jsc_id]:
            cls.BOKEH_CONTEXT[jsc._jsc_id]['Document'] = bokeh.plotting.Document()
            cls.BOKEH_CONTEXT[jsc._jsc_id]['Document_Index'] = 0

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
        df = df.copy()

        # setup X axis index in the dataframe
        if 'X' in df.columns:
            df = df.set_index('X')
        else:
            df.index.name = 'X'
        pv['df'] = df

        # generate the palette
        pv['palette'] = cls._configure_color_palette(pv['df'], kwargs.get('user_palette', None))

        # create the column data source for bokeh
        pv['df'].columns = pv['df'].columns.map(str)
        pv['cds'] = bokeh.models.ColumnDataSource(bokeh.models.ColumnDataSource.from_df(pv['df']))

        # compute the figure_kwargs
        figure_kwargs = cls._extract_targetclass_kwargs(bokeh.plotting.figure, kwargs, delete=True)
        figure_kwargs.update(cls._promote_kwargs_prefix(['__figure__'], figure_kwargs))
        pv['figure_kwargs'] = figure_kwargs

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
    def _create_hbar_chart_data(cls, pv, flip_factors=True):
        # init
        data = {}

        # convert
        df = pv['df'].copy()
        df.index = df.index.map(str)

        # build the factors
        data['factors'] = [(x, c) for x in df.index for c in df.columns]
        if flip_factors:
            data['factors'] = data['factors'][::-1]

        # build the data
        counts = []
        fill_color = []
        line_color = []
        for i, f in enumerate(data['factors']):
            idx = f[0]
            c = f[1]
            counts.append(df.loc[idx, c])
            nc = len(df.columns)
            if flip_factors:
                fill_color.append(pv['palette'][nc - 1 - (i % nc)])
                line_color.append(pv['palette'][nc - 1 - (i % nc)])
            else:
                fill_color.append(pv['palette'][i % nc])
                line_color.append(pv['palette'][i % nc])

        if len(df.columns) == 1:
            data['factors'] = [x[0] for x in data['factors']]

        data['cds'] = bokeh.models.ColumnDataSource({'factors': data['factors'], 'counts': counts,
                                                     'line_color': line_color, 'fill_color': fill_color})

        # success!
        return data

    @classmethod
    def _create_hbar_chart(cls, pv, **kwargs):
        """ Create a horizontal bar chart """
        # create the data
        data = cls._create_hbar_chart_data(pv)

        # create the figure
        p = bokeh.plotting.figure(y_range=bokeh.models.ranges.FactorRange(*data['factors']), **pv['figure_kwargs'])

        # plot the bars
        hbar_kwargs = dict(source=data['cds'], y='factors', right='counts', fill_color='fill_color', line_color='line_color', height=0.8)
        hbar_kwargs.update(cls._promote_kwargs_prefix(['__hbar__'], kwargs))

        p.hbar(**hbar_kwargs)

        # success!
        return p

    @classmethod
    def _create_line_chart_data(cls, pv):
        return {'cds': bokeh.models.ColumnDataSource(pv['df'])}

    @classmethod
    def _create_line_chart(cls, pv, **kwargs):
        """ Create a line chart """
        # create the data
        data = cls._create_line_chart_data(pv)

        # create the figure
        p = bokeh.plotting.figure(**pv['figure_kwargs'])

        # create the lines
        for i, c in enumerate(pv['df'].columns):
            line_kwargs = dict(source=data['cds'], x='X', y=c, color=pv['palette'][i], legend_label=c)
            line_kwargs.update(cls._promote_kwargs_prefix(['__line__', f'__line_{i}__'], kwargs))
            p.line(**line_kwargs)

        # success!
        return p

    @classmethod
    def _create_pie_chart_data(cls, pv):
        # recompute pv since a pie chart only works on the first row
        df = pv['df'].head(1).reset_index().T[1:]
        df = df.rename(columns={df.columns[0]: 'value'})
        df['angle'] = df['value'] / df['value'].sum() * 2 * math.pi
        df['color'] = pv['palette']
        df.index.name = 'legend'

        return {'cds': bokeh.models.ColumnDataSource(df)}

    @classmethod
    def _create_pie_chart(cls, pv, **kwargs):
        """ Create a pie chart """
        # create the data
        data = cls._create_pie_chart_data(pv)

        # create the figure
        p = bokeh.plotting.figure(**pv['figure_kwargs'])
        p.wedge(x=0, y=1, radius=0.4,
                start_angle=bokeh.transform.cumsum('angle', include_zero=True), end_angle=bokeh.transform.cumsum('angle'),
                line_color="white", fill_color='color', legend_field='legend', source=data['cds'])

        # don't show the grid or the axis
        p.axis.axis_label = None
        p.axis.visible = False
        p.grid.grid_line_color = None

        # success!
        return p

    @classmethod
    def _create_table_chart_data(cls, pv):
        return {'cds': bokeh.models.ColumnDataSource(pv['df'])}

    @classmethod
    def _create_table_chart(cls, pv, **kwargs):
        """ Create a line chart """
        # create the data
        data = cls._create_line_chart_data(pv)

        # plot the table
        table_kwargs = pv['figure_kwargs']
        table_kwargs.update({'source': data['cds']})
        table_kwargs.update(cls._promote_kwargs_prefix(['__table__'], kwargs))
        table_kwargs['columns'] = [bokeh.models.widgets.TableColumn(field=Ci, title=Ci) for Ci in pv['df'].columns]
        del table_kwargs['title']

        # # create the figure
        p = bokeh.models.widgets.DataTable(**table_kwargs)
#        p = DataTable(columns=columns, source=bokeh.models.ColumnDataSource(pv['df']))

        # success!
        return p

    @classmethod
    def _create_vbar_chart_data(cls, pv):
        return cls._create_hbar_chart_data(pv, flip_factors=False)

    @classmethod
    def _create_vbar_chart(cls, pv, **kwargs):
        """ Create a vertical bar chart """
        # create the data
        data = cls._create_vbar_chart_data(pv)

        # create the figure
        p = bokeh.plotting.figure(x_range=bokeh.models.ranges.FactorRange(*data['factors']), **pv['figure_kwargs'])

        # plot the bars
        vbar_kwargs = dict(source=data['cds'], x='factors', top='counts', fill_color='fill_color', line_color='line_color', width=0.8)
        vbar_kwargs.update(cls._promote_kwargs_prefix(['__vbar__'], kwargs))

        p.vbar(**vbar_kwargs)

        # success!
        return p

    def _create_chart(self, chart_type, jsc_id, **kwargs):
        # create the document if needed
        if jsc_id not in self.BOKEH_CONTEXT:
            self.BOKEH_CONTEXT[jsc_id] = {}
        if 'Document' not in self.BOKEH_CONTEXT[jsc_id]:
            self.BOKEH_CONTEXT[jsc_id]['Document'] = bokeh.plotting.Document()
            self.BOKEH_CONTEXT[jsc_id]['Document_Index'] = 0


        # call the sub function to actually generate the chart
        if hasattr(self, f'_create_{chart_type}_chart'):
            if self._get_data_handler:
                if 'df' not in kwargs:
                    kwargs['__creation'] = True
                    kwargs['df'] = self._get_data_handler(**kwargs)

            # prep for the chart
            pv = self._prep_for_chart(**kwargs)

            # create the chart
            p = getattr(self, f'_create_{chart_type}_chart')(pv, **kwargs)

            # add to the current document
            self.BOKEH_CONTEXT[jsc_id]['Document'].add_root(p)
            if 'Charts' not in self.BOKEH_CONTEXT[jsc_id]:
                self.BOKEH_CONTEXT[jsc_id]['Charts'] = {}
            if 'Charts_Doc_Index' not in self.BOKEH_CONTEXT[jsc_id]:
                self.BOKEH_CONTEXT[jsc_id]['Charts_Doc_Index'] = {}
            self.BOKEH_CONTEXT[jsc_id]['Charts'][p.id] = chart_type
            self.BOKEH_CONTEXT[jsc_id]['Charts_Doc_Index'][p.id] = self.BOKEH_CONTEXT[jsc_id]['Document_Index']
            self.BOKEH_CONTEXT[jsc_id]['Document_Index'] = self.BOKEH_CONTEXT[jsc_id]['Document_Index'] + 1

            # success!
            script, div = bokeh.embed.components(p)
            return script + div
        else:
            raise Exception(f'No chart type of "{chart_type}" is available')

    @classmethod
    def _update_chart(cls, jsc, chart_name, df):
        # update the data in the chart
        pv = cls._prep_for_chart(df = df)
        p_id = cls.BOKEH_CONTEXT[jsc._jsc_id]['Document'].get_model_by_name(chart_name).id
        chart_type = cls.BOKEH_CONTEXT[jsc._jsc_id]['Charts'][p_id]
        if chart_type == 'table':
            cds_id = cls.BOKEH_CONTEXT[jsc._jsc_id]['Document'].get_model_by_name(chart_name).source.id
        else:
            cds_id = cls.BOKEH_CONTEXT[jsc._jsc_id]['Document'].get_model_by_name(chart_name).renderers[0].data_source.id

        doc_index = cls.BOKEH_CONTEXT[jsc._jsc_id]['Charts_Doc_Index'][p_id]

        if hasattr(cls, f'_create_{chart_type}_chart_data'):
            func = getattr(cls, f'_create_{chart_type}_chart_data')
            data = func(pv)
            new_val = data['cds'].to_df().to_dict(orient='list')

            if chart_type == 'hbar':
                js = f"""Bokeh.documents[{doc_index}].get_model_by_id('{p_id}').y_range.factors = {json.dumps(data['factors'])};"""
                jsc.eval_js_code(js)
                js = f"""Bokeh.documents[{doc_index}].get_model_by_id('{cds_id}').data = {json.dumps(new_val)};"""
                jsc.eval_js_code(js)

            if chart_type == 'line':
                js = f"""Bokeh.documents[{doc_index}].get_model_by_id('{cds_id}').data = {json.dumps(new_val)};"""
                jsc.eval_js_code(js)

            if chart_type == 'pie':
                js = f"""Bokeh.documents[{doc_index}].get_model_by_id('{cds_id}').data = {json.dumps(new_val)};"""
                jsc.eval_js_code(js)

            if chart_type == 'table':
                js = f"""Bokeh.documents[{doc_index}].get_model_by_id('{cds_id}').data = {json.dumps(new_val)};"""
                jsc.eval_js_code(js)

            if chart_type == 'vbar':
                js = f"""Bokeh.documents[{doc_index}].get_model_by_id('{p_id}').x_range.factors = {json.dumps(data['factors'])};"""
                jsc.eval_js_code(js)
                js = f"""Bokeh.documents[{doc_index}].get_model_by_id('{cds_id}').data = {json.dumps(new_val)};"""
                jsc.eval_js_code(js)
