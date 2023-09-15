""" Plugin for Bokeh Applications """

# --------------------------------------------------
#    Imports
# --------------------------------------------------
import json
import math
import time
import uuid
import pandas as pd
import bokeh.embed
import bokeh.models
import bokeh.models.widgets
import bokeh.plotting
import bokeh.transform
import bokeh.models.formatters
from .bokehPlugin_util import promote_kwargs_prefix, configure_color_palette
from .bokehPlugin_hbar_chart import create_chart_js as create_hbar_chart_js
from .bokehPlugin_hbar_chart import update_chart_js as update_hbar_chart_js
from .bokehPlugin_line_chart import create_chart_js as create_line_chart_js
from .bokehPlugin_line_chart import update_chart_js as update_line_chart_js
from .bokehPlugin_pie_chart import create_chart_js as create_pie_chart_js
from .bokehPlugin_pie_chart import update_chart_js as update_pie_chart_js
from .bokehPlugin_vbar_chart import create_chart_js as create_vbar_chart_js
from .bokehPlugin_vbar_chart import update_chart_js as update_vbar_chart_js
from .bokehPlugin_histogram_chart import create_chart_js as create_histogram_chart_js
from .bokehPlugin_histogram_chart import update_chart_js as update_histogram_chart_js
from .bokehPlugin_table_chart import create_chart_js as create_table_chart_js
from .bokehPlugin_table_chart import update_chart_js as update_table_chart_js

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
        pass
#        del cls.BOKEH_CONTEXT[jsc.page_instance_id]

    @classmethod
    def on_context_open(cls, jsc):
        # create a new bokeh document if needed for this js client.  this may have been created
        # during page template rendering
        if jsc.page_instance_id not in cls.BOKEH_CONTEXT:
            cls.BOKEH_CONTEXT[jsc.page_instance_id] = {}
        if 'Document' not in cls.BOKEH_CONTEXT[jsc.page_instance_id]:
            cls.BOKEH_CONTEXT[jsc.page_instance_id]['Document'] = bokeh.plotting.Document()
            cls.BOKEH_CONTEXT[jsc.page_instance_id]['Document_Index'] = 0

    # --------------------------------------------------
    #    Private Functions
    # --------------------------------------------------
    # @classmethod
    # def _configure_color_palette(cls, df, user_palette=None):
    #     """ configure a list of colors to rotate through on the charts
    #
    #         Args:
    #             df - dataframe containing data
    #             user_palette - a user supplied 2D palette, default is bokeh Category10
    #
    #         Returns:
    #             a normalized palette large enough to color the data
    #     """
    #     # setup the base palette
    #     if user_palette is None:
    #         user_palette = bokeh.palettes.Category10
    #
    #     # calculate colors needed
    #     colors_needed = 0
    #     for c in df.columns.map(str):
    #         if not c.startswith('_'):
    #             colors_needed = colors_needed + 1
    #
    #     # calculate best color range in palette
    #     cr_min = sorted(user_palette.keys())[0]
    #     cr_max = sorted(user_palette.keys())[-1]
    #     color_range = min(cr_max, max(cr_min, colors_needed))
    #
    #     # calculate number of colors available in that color range
    #     cr_colors_available = len(user_palette[color_range])
    #
    #     # generate palette
    #     palette = []
    #     for i in range(0, colors_needed):
    #         palette.append(user_palette[color_range][i % cr_colors_available])
    #
    #     # success!
    #     return palette

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
        # if df.empty:
        #     df = pd.DataFrame(data=[[0]], columns=['Blank'])
        df = df.copy()

        # setup X axis index in the dataframe
        if 'X' in df.columns:
            df = df.set_index('X')
        else:
            df.index.name = 'X'
        pv['df'] = df

        # generate the palette
        pv['palette'] = configure_color_palette(pv['df'], kwargs.get('user_palette', None))

        # create the column data source for bokeh
        pv['df'].columns = pv['df'].columns.map(str)
        pv['cds'] = bokeh.models.ColumnDataSource(bokeh.models.ColumnDataSource.from_df(pv['df']))

        # compute the figure_kwargs
        figure_kwargs = cls._extract_targetclass_kwargs(bokeh.plotting.figure, kwargs, delete=True)
        figure_kwargs.update(promote_kwargs_prefix(['__figure__'], kwargs))
        # if 'x_axis_type' in kwargs:
        #     figure_kwargs['x_axis_type'] = kwargs['x_axis_type']
        pv['figure_kwargs'] = figure_kwargs

        # success!
        return pv

    # @classmethod
    # def _promote_kwargs_prefix(cls, prefixes, kwargs):
    #     """ return keyword args that start with a prefix.  the returned dictionary will have the prefix strippped
    #
    #         Args:
    #             prefixes - list of prefixes to match for, i.e. '__figure__', '__figure(0)__'
    #             kwargs - keyword args dictionary
    #
    #         Returns:
    #             dictionary containing the found keyword args but with the prefix stripped off
    #     """
    #     promoted = {}
    #     for k in kwargs.keys():
    #         for p in prefixes[::-1]:
    #             if k.startswith(p):
    #                 promoted[k[len(p):]] = kwargs[k]
    #                 break
    #     return promoted

    # --------------------------------------------------
    #    Chart Creation Functions
    # --------------------------------------------------
    # @classmethod
    # def _create_hbar_chart_data(cls, pv, flip_factors=True):
    #     # init
    #     data = {}
    #
    #     # convert
    #     df = pv['df'].copy()
    #     df.index = df.index.map(str)
    #
    #     # build the factors
    #     data['factors'] = [(x, c) for x in df.index for c in df.columns]
    #     if flip_factors:
    #         data['factors'] = data['factors'][::-1]
    #
    #     # build the data
    #     counts = []
    #     fill_color = []
    #     line_color = []
    #     for i, f in enumerate(data['factors']):
    #         idx = f[0]
    #         c = f[1]
    #         counts.append(df.loc[idx, c])
    #         nc = len(df.columns)
    #         if flip_factors:
    #             fill_color.append(pv['palette'][nc - 1 - (i % nc)])
    #             line_color.append(pv['palette'][nc - 1 - (i % nc)])
    #         else:
    #             fill_color.append(pv['palette'][i % nc])
    #             line_color.append(pv['palette'][i % nc])
    #
    #     if len(df.columns) == 1:
    #         data['factors'] = [x[0] for x in data['factors']]
    #
    #     data['cds'] = bokeh.models.ColumnDataSource({'factors': data['factors'], 'counts': counts,
    #                                                  'line_color': line_color, 'fill_color': fill_color})
    #
    #     # success!
    #     return data
    #
    # @classmethod
    # def _create_hbar_chart(cls, pv, **kwargs):
    #     """ Create a horizontal bar chart """
    #     # create the data
    #     data = cls._create_hbar_chart_data(pv)
    #
    #     # create the figure
    #     p = bokeh.plotting.figure(y_range=bokeh.models.ranges.FactorRange(*data['factors']), **pv['figure_kwargs'])
    #
    #     # plot the bars
    #     hbar_kwargs = dict(source=data['cds'], y='factors', right='counts', fill_color='fill_color', line_color='line_color', height=0.8)
    #     hbar_kwargs.update(cls._promote_kwargs_prefix(['__hbar__'], kwargs))
    #
    #     p.hbar(**hbar_kwargs)
    #
    #     # success!
    #     return p

    @classmethod
    def _create_line_chart_data(cls, pv):
        """
                    A   B   C
                X            
                0  21   3  24
                1  60  24  64
                2  72  68  13
        """
        return {'cds': bokeh.models.ColumnDataSource(pv['df'])}
    
    # @classmethod
    # def _create_line_chart_js(cls, target_div_id, pv, **kwargs):
    #     """ Create the javascript to create a line chart """
    #     js = f"""
    #         var plt = Bokeh.Plotting;
    #         var f = new plt.Figure({pv['figure_kwargs']});
    #         """        
    #     js += cls._update_line_chart_js(pv, **kwargs)
    #     js += f"plt.show(f, '#{target_div_id}');"
    #
    #     return js
    #
    # @classmethod
    # def _update_line_chart_js(cls, pv, chart_name=None, **kwargs):
    #     cds_data_json = json.dumps(pv['df'].reset_index().to_dict(orient='list'))
    #     js = f"""
    #         var plt = Bokeh.Plotting;
    #         var data_json = JSON.parse('{cds_data_json}');
    #         var cds = new Bokeh.ColumnDataSource({{'data': data_json}});
    #     """
    #
    #     if chart_name is not None:
    #         js += f"""
    #         var f;
    #
    #         for (let i = 0; i < Bokeh.documents.length; i++) {{
    #             f = Bokeh.documents[i].get_model_by_name('{chart_name}');
    #             if (f != null) {{
    #                 break;
    #             }}
    #         }}
    #     """ 
    #
    #     # remove the old glyphs
    #     js += """
    #         for (let i = f.renderers.length - 1; i >= 0; i--) {
    #             f.renderers[i].visible = false;
    #             f.renderers.pop();
    #             f.legend.items.pop();
    #         }
    #         f.legend.change.emit();
    #     """                
    #
    #     for i, c in enumerate(pv['df'].columns):
    #         kwd = {}
    #         kwd['source'] = 'cds'
    #         kwd['x'] = "{field: 'X'}"
    #         kwd['y'] = f"{{field: '{c}'}}"
    #         kwd['color'] = f"'{pv['palette'][i]}'"
    #         kwd.update(cls._promote_kwargs_prefix(['__line__', f'__line_{i}__'], kwargs))
    #         kwds = ', '.join([f"'{k}': {v}" for k, v in kwd.items()])
    #
    #         js += f"""
    #             // add the line    
    #             var lo = f.line({{ {kwds} }});
    #
    #             // add the legend item
    #             var lio = new Bokeh.LegendItem({{label: '{c}'}});
    #             lio.renderers.push(lo);
    #             f.legend.items.push(lio);
    #             f.legend.change.emit();
    #         """
    #     return js

        


#     @classmethod
#     def _create_line_chart(cls, pv, **kwargs):
#         """ Create a line chart """
#         print(kwargs)
#
#         j = cls._create_line_chart_js('xxx', pv, **kwargs)
#         print(j)
#
#         # create the data
#         data = cls._create_line_chart_data(pv)
#
#         # create the figure
#         p = bokeh.plotting.figure(**pv['figure_kwargs'])
#
#         # create the lines
#         line_kwargs_list = []
#         for i, c in enumerate(pv['df'].columns):
#             line_kwargs = dict(source=data['cds'], x='X', y=c, color=pv['palette'][i], legend_label=c)
#             line_kwargs.update(cls._promote_kwargs_prefix(['__line__', f'__line_{i}__'], kwargs))
#             p.line(**line_kwargs)
#             line_kwargs_list.append(line_kwargs)
#
#         # attach extra information so we can create new lines if needed later
# #        tag_pv = {k:pv[k] for k in pv if k not in ('df', 'cds')}
#         # tag_pv = {}
#         # p.tags.append({'pv': tag_pv, 'cds_id': data['cds'].id, 'line_kwargs_list': line_kwargs_list})
#
#         p.y_range.start = 0
#         p.yaxis.formatter=bokeh.models.formatters.NumeralTickFormatter(format="0,0")
#
#         # success!
#         return p

    # @classmethod
    # def _update_line_chart(cls, pv, **kwargs):
    #     # generate the javascript code to update the line chart
    #     js = f"""
    #             plt = Bokeh.Plotting;
    #             fig = Bokeh.documents[{doc_index}].get_model_by_id('{cds_id}').data = {json.dumps(new_val)};"""
    #     #         jsc.eval_js_code(js)
    #     #
    #     # """
        

    # @classmethod
    # def _create_pie_chart_data(cls, pv):
    #     # recompute pv since a pie chart only works on the first row
    #     df = pv['df'].head(1).reset_index().T[1:]
    #     df = df.rename(columns={df.columns[0]: 'value'})
    #     df['angle'] = df['value'] / df['value'].sum() * 2 * math.pi
    #     df['text_angle'] = (df['value'] / df['value'].sum() * 2 * math.pi)
    #     df['color'] = pv['palette']
    #     df["text_value"] = df['value'].astype(str)
    #     df["text_value"] = df["text_value"].str.pad(12, side = "left")
    #
    #     df.index.name = 'legend'
    #
    #     return {'cds': bokeh.models.ColumnDataSource(df)}
    #
    # @classmethod
    # def _create_pie_chart(cls, pv, **kwargs):
    #     """ Create a pie chart """
    #     # create the data
    #     data = cls._create_pie_chart_data(pv)
    #
    #     # create the figure
    #     p = bokeh.plotting.figure(**pv['figure_kwargs'])
    #     p.wedge(x=0, y=1, radius=0.4,
    #             start_angle=bokeh.transform.cumsum('angle', include_zero=True), end_angle=bokeh.transform.cumsum('angle'),
    #             line_color="white", fill_color='color', legend_field='legend', source=data['cds'])
    #
    #     labels = bokeh.models.LabelSet(x=0, y=1, text='text_value',
    #                       angle=bokeh.transform.cumsum('text_angle', include_zero=True), source=data['cds'], text_color='white')
    #     p.add_layout(labels)
    #
    #     # don't show the grid or the axis
    #     p.axis.axis_label = None
    #     p.axis.visible = False
    #     p.grid.grid_line_color = None
    #
    #     # success!
    #     return p

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
        table_kwargs.update(promote_kwargs_prefix(['__table__'], kwargs))
        table_kwargs['columns'] = [bokeh.models.widgets.TableColumn(field=Ci, title=Ci) for Ci in pv['df'].columns]
        del table_kwargs['title']

        # # create the figure
        p = bokeh.models.widgets.DataTable(**table_kwargs)
#        p = DataTable(columns=columns, source=bokeh.models.ColumnDataSource(pv['df']))

        # success!
        return p

    # @classmethod
    # def _create_varea_chart_data(cls, pv):
    #     return {'cds': bokeh.models.ColumnDataSource(pv['df'])}
    #
    # @classmethod
    # def _create_varea_chart(cls, pv, **kwargs):
    #     """ Create a vertical stacked area chart """
    #     # create the data
    #     data = cls._create_varea_chart_data(pv)
    #
    #     # create the figure
    #     p = bokeh.plotting.figure(**pv['figure_kwargs'])
    #
    #     # create the vertical area
    #     p.varea_stack(stackers=pv['df'].columns, x='X', source=data['cds'], color=pv['palette'], legend_label=[str(c) for c in pv['df'].columns])
    #
    #     # success!
    #     return p

    # @classmethod
    # def _create_vbar_chart_data(cls, pv):
    #     return cls._create_hbar_chart_data(pv, flip_factors=False)
    #
    # @classmethod
    # def _create_vbar_chart(cls, pv, **kwargs):
    #     """ Create a vertical bar chart """
    #     # create the data
    #     data = cls._create_vbar_chart_data(pv)
    #
    #     # create the figure
    #     p = bokeh.plotting.figure(x_range=bokeh.models.ranges.FactorRange(*data['factors']), **pv['figure_kwargs'])
    #
    #     # plot the bars
    #     vbar_kwargs = dict(source=data['cds'], x='factors', top='counts', fill_color='fill_color', line_color='line_color', width=0.8)
    #     vbar_kwargs.update(cls._promote_kwargs_prefix(['__vbar__'], kwargs))
    #
    #     p.vbar(**vbar_kwargs)
    #
    #     # success!
    #     return p

    # @classmethod
    # def _create_histogram_chart_data(cls, pv):
    #     # init, grab the first color off the palette using a fake dataframe
    #     data = {}
    #     palette = cls._configure_color_palette(pd.DataFrame(index=[0], columns=['A']))
    #
    #     # sanity check
    #     if list(pv['df'].columns) == ['Blank']:
    #         pv['df'] = pd.DataFrame(index=['0'])
    #         pv['df']['counts'] = 1
    #
    #     # convert
    #     df = pv['df'].copy()
    #     df.index.name = 'factors'
    #     df = df.reset_index()
    #     df['fill_color'] = palette[0]
    #     df['line_color'] = palette[0]
    #     df['counts_text'] = df['counts']
    #     data['df'] = df
    #     data['cds'] = bokeh.models.ColumnDataSource(df)
    #
    #     # success!
    #     return data
    #
    # @classmethod
    # def _create_histogram_chart(cls, pv, **kwargs):
    #     """ Create a histogram bar chart """
    #     # create the data
    #     data = cls._create_histogram_chart_data(pv)
    #
    #     # create the figure
    #     p = bokeh.plotting.figure(x_range=bokeh.models.ranges.FactorRange(*data['cds'].data['factors']), **pv['figure_kwargs'])
    #
    #     # plot the bars
    #     histogram_kwargs = dict(source=data['cds'], x='factors', top='counts', fill_color='fill_color', line_color='line_color', width=0.95)
    #     histogram_kwargs.update(cls._promote_kwargs_prefix(['__histogram__'], kwargs))
    #
    #     # add labelset
    #     labels = bokeh.models.LabelSet(x='factors', y='counts_text', text='bin_text', level='glyph',
    #                       text_align='center', y_offset=5, source=data['cds'])
    #     p.add_layout(labels)
    #
    #     p.vbar(**histogram_kwargs)
    #     p.x_range.range_padding = 0.05
    #     p.y_range = bokeh.models.Range1d(start=0, end=data['df']['counts'].max() * 1.1)
    #
    #     # success!
    #     return p

    def _create_chart(self, chart_type, page_instance_id, jsc_sequence_number=0, **kwargs):
        # create the document if needed
        if page_instance_id not in self.BOKEH_CONTEXT:
            self.BOKEH_CONTEXT[page_instance_id] = {}
            self.BOKEH_CONTEXT[page_instance_id]['Figures'] = {}
            self.BOKEH_CONTEXT[page_instance_id]['kwargs'] = {}
        if 'Document' not in self.BOKEH_CONTEXT[page_instance_id]:
            self.BOKEH_CONTEXT[page_instance_id]['Document'] = bokeh.plotting.Document()
            self.BOKEH_CONTEXT[page_instance_id]['Document_Index'] = 0

        if chart_type == 'line':
            pv = self._prep_for_chart(**kwargs)
            self.BOKEH_CONTEXT[page_instance_id]['Figures'][kwargs['name']] = chart_type
            self.BOKEH_CONTEXT[page_instance_id]['kwargs'][kwargs['name']] = kwargs
            div_id = f"div_{kwargs['name']}"
            div = f"<div id={div_id} style='margin:0 px; padding: 0px; width:100%; height:100%;'></div>"
            script = f"<script>{create_line_chart_js(div_id, pv, **kwargs)}</script>"
            return div + script
        if chart_type == 'pie':
            pv = self._prep_for_chart(**kwargs)
            self.BOKEH_CONTEXT[page_instance_id]['Figures'][kwargs['name']] = chart_type
            self.BOKEH_CONTEXT[page_instance_id]['kwargs'][kwargs['name']] = kwargs
            div_id = f"div_{kwargs['name']}"
            div = f"<div id={div_id} style='margin:0 px; padding: 0px; width:100%; height:100%;'></div>"
            script = f"<script>{create_pie_chart_js(div_id, pv, **kwargs)}</script>"
            return div + script
        if chart_type == 'hbar':
            pv = self._prep_for_chart(**kwargs)
            self.BOKEH_CONTEXT[page_instance_id]['Figures'][kwargs['name']] = chart_type
            self.BOKEH_CONTEXT[page_instance_id]['kwargs'][kwargs['name']] = kwargs
            div_id = f"div_{kwargs['name']}"
            div = f"<div id={div_id} style='margin:0 px; padding: 0px; width:100%; height:100%;'></div>"
            script = f"<script>{create_hbar_chart_js(div_id, pv, **kwargs)}</script>"
            return div + script
        if chart_type == 'vbar':
            pv = self._prep_for_chart(**kwargs)
            self.BOKEH_CONTEXT[page_instance_id]['Figures'][kwargs['name']] = chart_type
            self.BOKEH_CONTEXT[page_instance_id]['kwargs'][kwargs['name']] = kwargs
            div_id = f"div_{kwargs['name']}"
            div = f"<div id={div_id} style='margin:0 px; padding: 0px; width:100%; height:100%;'></div>"
            script = f"<script>{create_vbar_chart_js(div_id, pv, **kwargs)}</script>"
            return div + script
        if chart_type == 'histogram':
            pv = self._prep_for_chart(**kwargs)
            self.BOKEH_CONTEXT[page_instance_id]['Figures'][kwargs['name']] = chart_type
            self.BOKEH_CONTEXT[page_instance_id]['kwargs'][kwargs['name']] = kwargs
            div_id = f"div_{kwargs['name']}"
            div = f"<div id={div_id} style='margin:0 px; padding: 0px; width:100%; height:100%;'></div>"
            script = f"<script>{create_histogram_chart_js(div_id, pv, **kwargs)}</script>"
            return div + script
        if chart_type == 'table':
            pv = self._prep_for_chart(**kwargs)
            self.BOKEH_CONTEXT[page_instance_id]['Figures'][kwargs['name']] = chart_type
            self.BOKEH_CONTEXT[page_instance_id]['kwargs'][kwargs['name']] = kwargs
            div_id = f"div_{kwargs['name']}"
            div = f"<div id={div_id} style='margin:0 px; padding: 0px; width:100%; height:100%;'></div>"
            script = f"<script>{create_table_chart_js(div_id, pv, **kwargs)}</script>"
            return div + script


        # call the sub function to actually generate the chart
        if hasattr(self, f'_create_{chart_type}_chart'):
            if self._get_data_handler:
                if 'df' not in kwargs:
                    kwargs['__creation'] = True
                    kwargs['df'] = self._get_data_handler(page_instance_id, jsc_sequence_number=jsc_sequence_number, **kwargs)

            # prep for the chart
            pv = self._prep_for_chart(**kwargs)

            # # success!
            # if chart_type == 'line':
            #     self.BOKEH_CONTEXT[jsc_id]['Figures'][kwargs['name']] = chart_type
            #     div_id = f"div_{kwargs['name']}"
            #     div = f"<div id={div_id} style='margin:0 px; padding: 0px; width:100%; height:100%;'></div>"
            #     script = f"<script>{self._create_line_chart_js(div_id, pv, **kwargs)}</script>"
            #     return div + script
    
    

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


            
            
            script, div = bokeh.embed.components(p)
            return script + div
        else:
            raise Exception(f'No chart type of "{chart_type}" is available')



    @classmethod
    def _update_chart(cls, jsc, chart_name, df):
        # update the data in the chart
        pv = cls._prep_for_chart(df = df)
        
        # new style update
        # ---------------
        if chart_name in cls.BOKEH_CONTEXT[jsc.page_instance_id]['Figures']:
            chart_type = cls.BOKEH_CONTEXT[jsc.page_instance_id]['Figures'][chart_name]
            if chart_name in cls.BOKEH_CONTEXT[jsc.page_instance_id]['kwargs']:
                kwargs = cls.BOKEH_CONTEXT[jsc.page_instance_id]['kwargs'][chart_name]
            else:
                kwargs = {}

            if chart_type == 'line':                 
                js = update_line_chart_js(pv, chart_name, **kwargs)
                jsc.eval_js_code(js, blocking=False)
                return
            if chart_type == 'pie':                 
                js = update_pie_chart_js(pv, **kwargs)
                jsc.eval_js_code(js, blocking=False)
                return
            if chart_type == 'hbar':                 
                js = update_hbar_chart_js(pv, chart_name, **kwargs)
                jsc.eval_js_code(js, blocking=False)
                return
            if chart_type == 'vbar':
                js = update_vbar_chart_js(pv, chart_name, **kwargs)
                jsc.eval_js_code(js, blocking=False)
                return
            if chart_type == 'histogram':
                js = update_histogram_chart_js(pv, chart_name, **kwargs)
                jsc.eval_js_code(js, blocking=False)
                return
            if chart_type == 'table':
                js = update_table_chart_js(pv, chart_name, **kwargs)
                jsc.eval_js_code(js, blocking=False)
                return
        
        
        p_id = cls.BOKEH_CONTEXT[jsc.page_instance_id]['Document'].get_model_by_name(chart_name).id
        chart_type = cls.BOKEH_CONTEXT[jsc.page_instance_id]['Charts'][p_id]
        if chart_type == 'table':
            cds_id = cls.BOKEH_CONTEXT[jsc.page_instance_id]['Document'].get_model_by_name(chart_name).source.id
        else:
            cds_id = cls.BOKEH_CONTEXT[jsc.page_instance_id]['Document'].get_model_by_name(chart_name).renderers[0].data_source.id

        doc_index = cls.BOKEH_CONTEXT[jsc.page_instance_id]['Charts_Doc_Index'][p_id]

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
                # update the data in javascript
                js = f"""Bokeh.documents[{doc_index}].get_model_by_id('{cds_id}').data = {json.dumps(new_val)};"""
                jsc.eval_js_code(js)

                # add another line glyph if needed
                p = cls.BOKEH_CONTEXT[jsc.page_instance_id]['Document'].get_model_by_name(chart_name)
                palette = cls._configure_color_palette(df)
                for i in range(1, len(pv['cds'].column_names)):
                    if i > len(p.renderers):
                        c = pv['cds'].column_names[i]
                        line_kwargs = dict(source=pv['cds'], x='X', y=c, color=palette[i - 1], legend_label=c)
                        p.line(**line_kwargs)

                        js = f"""
                            // create a new line
                            var line = new Bokeh.Line({{x: {{ field: "X" }},
                                                        y: {{ field: "{c}" }},
                                                        line_color: "{palette[i - 1]}",
                                                        line_width: 2}});
                            var plot = Bokeh.documents[{doc_index}].get_model_by_id('{p_id}');
                            var cds = Bokeh.documents[{doc_index}].get_model_by_id('{cds_id}');
                            plot.add_glyph(line, cds);

                            // create a new legend item for the line
                            var legends = Bokeh.documents[{doc_index}].get_model_by_id('{p.legend.id}');
                            var legenditem = new Bokeh.LegendItem({{label: "{c}"}});
                            legends.items.push(legenditem);
                            legenditem.renderers.push(plot.renderers[plot.renderers.length - 1]);
                            legends.change.emit();"""
                        print(js)
                        jsc.eval_js_code(js)
                    else:
                        # make visible any hidden lines and legends
                        js = f"""
                            var plot = Bokeh.documents[{doc_index}].get_model_by_id('{p_id}');
                            var legends = Bokeh.documents[{doc_index}].get_model_by_id('{p.legend.id}');

                            plot.renderers[{i - 1}].visible = true;
                            legends.items[{i - 1}].visible = true;
                            legends.change.emit();"""
                        print(js)
                        jsc.eval_js_code(js)

                # hide and lines and legends not needed
                print('***', len(pv['cds'].column_names), len(p.renderers))
                for i in range(len(p.renderers), len(pv['cds'].column_names) - 1, -1):
                    js = f"""
                        var plot = Bokeh.documents[{doc_index}].get_model_by_id('{p_id}');
                        var legends = Bokeh.documents[{doc_index}].get_model_by_id('{p.legend.id}');

                        plot.renderers[{i - 1}].visible = false;
                        legends.items[{i - 1}].visible = false;"""
                    print(js)
                    jsc.eval_js_code(js)

            if chart_type == 'pie':
                js = f"""Bokeh.documents[{doc_index}].get_model_by_id('{cds_id}').data = {json.dumps(new_val)};"""
                jsc.eval_js_code(js)

            if chart_type == 'table':

                js = f"""
                var cds;
                
                for (let i = 0; i < Bokeh.documents.length; i++) {{
                    cds = Bokeh.documents[i].get_model_by_id('{cds_id}');
                    if (cds != null) {{
                        break;
                    }}
                }}
                
                cds.data = {json.dumps(new_val)};
    """ 

                
#                js = f"""Bokeh.documents[{doc_index}].get_model_by_id('{cds_id}').data = {json.dumps(new_val)};"""
                jsc.eval_js_code(js)

            if chart_type == 'varea':
                js = f"""Bokeh.documents[{doc_index}].get_model_by_id('{cds_id}').data = {json.dumps(new_val)};"""
                jsc.eval_js_code(js)

            if chart_type == 'vbar':
                js = f"""Bokeh.documents[{doc_index}].get_model_by_id('{p_id}').x_range.factors = {json.dumps(data['factors'])};"""
                jsc.eval_js_code(js)
                js = f"""Bokeh.documents[{doc_index}].get_model_by_id('{cds_id}').data = {json.dumps(new_val)};"""
                jsc.eval_js_code(js)

            if chart_type == 'histogram':
                js = f"""Bokeh.documents[{doc_index}].get_model_by_id('{p_id}').y_range.end={data['df']['counts'].max() * 1.1}"""
                jsc.eval_js_code(js)
                js = f"""Bokeh.documents[{doc_index}].get_model_by_id('{cds_id}').data = {json.dumps(new_val)};"""
                jsc.eval_js_code(js)
