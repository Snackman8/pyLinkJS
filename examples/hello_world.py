import random
import pylinkjs

async def button_clicked(context_id, a, b, c):
    js_code = """document.getElementById("divout").innerHTML="%s";""" % (random.random())
    retval = await pylinkjs.eval_js_code(context_id, js_code)
    print(retval)

pylinkjs.run(default_html='hello_world.html')
