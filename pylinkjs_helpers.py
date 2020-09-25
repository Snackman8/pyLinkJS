from pylinkjs import eval_js_code


def escape_quotes(s):
    """ convert all single and double quotes to backslash single quote and backslash double quote """
    s = s.replace("'", "\\'")
    s = s.replace('"', '\\"')
    return s

async def add_class(context, id_list, classname):
    if isinstance(id_list, str):
        jscode = """if (!(document.getElementById('%s').classList.contains('%s'))) { document.getElementById('%s').classList.add('%s'); }""" % (id_list, classname, id_list, classname)
        await eval_js_code(context, jscode)        
    else:
        for i in id_list:
            await add_class(context, i, classname)

async def remove_class(context, id_list, classname):
    if isinstance(id_list, str):
        jscode = """if ((document.getElementById('%s').classList.contains('%s'))) { document.getElementById('%s').classList.remove('%s'); }""" % (id_list, classname, id_list, classname)
        await eval_js_code(context, jscode)        
    else:
        for i in id_list:
            await remove_class(context, i, classname)

async def set_disabled(context, id_list, new_value=True):
    if isinstance(id_list, str):
        jscode = """document.getElementById('%s').disabled=%s""" % (id_list, 'true' if new_value == True else 'false')
        await eval_js_code(context, jscode)        
    else:
        for i in id_list:
            await set_disabled(context, i, new_value)

async def set_disabled_by_class(context, class_name, new_value=True):
    jscode = """var els = document.getElementsByClassName('%s');
                 for (var i=0; i < els.length; i++) {
                     els[i].disabled = %s;
                 }""" % (class_name, 'true' if new_value == True else 'false')
    await eval_js_code(context, jscode)        

async def get_attr(context, element_id, attr):
    jscode = """document.getElementById('%s').%s""" % (element_id, attr)    
    return await eval_js_code(context, jscode)

async def set_attr(context, element_id, attr, new_value, no_wait=False):
    if isinstance(new_value, str):
        new_value = '"%s"' % (new_value.replace('"', '\\"'))
    jscode = """document.getElementById('%s').%s = %s""" % (element_id, attr, new_value)    
    return await eval_js_code(context, jscode, no_wait)

async def get_select_options(context, select_id):
    jscode = """Array.from(document.getElementById('%s').options).map(x => x.text)""" % select_id    
    return await eval_js_code(context, jscode)


async def set_select_options(context, select_id, options_list):
    jscode = """
        var sel = document.getElementById('%s');
        
        while (sel.options.length > 0) { sel.remove(0); }
        
        var new_opts = [%s];
        
        for (var i = 0; i < new_opts.length; i++) {
            var opt = document.createElement('option');
            opt.text = new_opts[i];
            opt.value = new_opts[i];
            sel.add(opt, null);
        }""" % (select_id, ','.join(['"%s"' % x for x in options_list]))
    return await eval_js_code(context, jscode)
