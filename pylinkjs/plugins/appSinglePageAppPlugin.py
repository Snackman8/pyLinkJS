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
    
    def show_pane(self, jsc, pane_id, **kwargs):
        """ exposed function to bind to the jsc """
        # show and hide the correct panes
        for p in jsc.get_setting('SinglePageApp_Panes'):
            if p.__name__ == pane_id:
                if hasattr(p, 'init_pane'):
                    p.init_pane(jsc, **kwargs)
            jsc.eval_js_code(f"""$('#{p.__name__}').css('display', '{"block" if p.__name__ == pane_id else "none"}')""")

        # change the history state since this is a Single Page App
        jsc.eval_js_code(f"""history.pushState({{'pane': '{pane_id}'}}, '', '/')""")


def popstate(jsc, state, target):
    """ called when the webpage is transitioned to using the back or forward buttons on the browser.

        For single page apps, the state should be used to change the state of the page to mimic a back
        or forward button page movement

        Args:
            state - state of the page to transition to, i.e. "show_login"
            target - target url the page is transitioning to, i.e. "https://www.myapp.com/"
    """
    jsc.show_pane(state.get('pane'))
