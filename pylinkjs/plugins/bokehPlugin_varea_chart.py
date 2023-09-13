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
