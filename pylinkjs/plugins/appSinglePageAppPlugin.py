""" Plugin for Single Page Applications """

# --------------------------------------------------
#    Plugin
# --------------------------------------------------
class pluginSinglePageApp:
    """ plugin for single page application """

    def __init__(self, panes):
        """ init """
        self._kwargs = {
            'SinglePageApp_Panes': panes }
        self.jsc_exposed_funcs = {'show_pane': self.show_pane}

    def register(self, kwargs):
        """ callback to register this plugin with the framework """
        # merge the dictionaries
        kwargs.update(self._kwargs)
    
    def show_pane(self, jsc, pane_id):
        """ exposed function to bind to the jsc """
        # show and hide the correct panes
        for p in jsc.get_setting('SinglePageApp_Panes'):
            if p.__name__ == pane_id:
                if hasattr(p, 'init_pane'):
                    p.init_pane(jsc)
            jsc.eval_js_code(f"""$('#{p.__name__}').css('display', '{"block" if p.__name__ == pane_id else "none"}')""")

        # change the history state since this is a Single Page App
        jsc.eval_js_code(f"""history.pushState({{'pane': '{pane_id}'}}, '', '/')""")
