import random
from pylinkjs import eval_js_code, run_pylinkjs_app


async def button_clicked(context_id, a, b, c):
    js_code = """document.getElementById("divout").innerHTML="%s";""" % (random.random())
    retval = await eval_js_code(context_id, js_code)
    print(retval)

run_pylinkjs_app(default_html='hello_world.html')
