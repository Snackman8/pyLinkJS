from pylinkjs import run_pylinkjs_app, Code


def ready(jsc, *args):
    print('Ready', args)


def button_clicked(jsc, a, b, c):
    retval = jsc.eval_js_code(77)
    print('GOT BACK', retval)
    print('TEST', jsc['#divout'].html)
    jsc['#divout'].html = 'AS"\'DF2'
    jsc['#divout'].css.color = 'red'
    jsc['#divout'].click = Code('function() { console.log("AA"); }')
    jsc['#divout2'].html = """<select id="AAA"><option>A</option><option>B</option></select>"""
    jsc['#AAA'].change = Code('function() { call_py("py_select_changed", $("#AAA").val(), 2, 3); }')


def py_select_changed(jsc, a, b, c):
    print(a, b, c)


run_pylinkjs_app(default_html='hello_world.html')
