# --------------------------------------------------
#    Imports
# --------------------------------------------------
import logging
import math
import os
try:
    from .business_logic import delete_record, init_data, get_record_count, get_record_for_updating, get_records_for_display, resort_data, update_record
except: 
    from business_logic import delete_record, init_data, get_record_count, get_record_for_updating, get_records_for_display, resort_data, update_record
from pylinkjs.PyLinkJS import run_pylinkjs_app


# --------------------------------------------------
#    Functions
# --------------------------------------------------
def _refresh_view(jsc):
    """ refresh the table view """
    # crop to only the page and number of records we want to show
    starting_index = (jsc.tag['page'] - 1) * jsc.tag['records_per_page']
    df_view = get_records_for_display(jsc.tag['data_props'], starting_index, jsc.tag['records_per_page'])
    
    # generate the html to show
    html = '<table>'
    html += f"""<tr><th></th><th class=th_header onclick="call_py('on_header_clicked', 0);">PK</th>"""
    html += ''.join([f"""<th class=th_header onclick="call_py('on_header_clicked', {i + 1});">{x}</th>""" for i, x in enumerate(df_view.columns)]) + '</tr>'    
                     
    html_rows = []
    for pk, r in df_view.iterrows():
        s = '<tr>'
        s += f"""<td class=td_data><button class=edit_button onclick="call_py('on_edit_button_clicked', '{pk}');">Edit</button>"""
        s += f"""<button class=delete_button onclick="call_py('on_delete_button_clicked', '{pk}');">Delete</button></td>"""
        s += f'<td class=td_data>{pk}</td>' + ''.join(f'<td class=td_data>{x}</td>' for x in r)
        s += '</tr>'
        html_rows.append(s)
    html += '\n'.join(html_rows)
    html += '<table>'
    
    # add page selectors
    html_pages = """<div class=page_selectors><button class=page_button onclick="call_py('on_change_page_clicked', 'Prev');">Prev Page</button><button onclick="call_py('on_change_page_clicked', 'Next');">Next Page</button>"""
    for i in range(1, jsc.tag['max_page'] + 1):
        c = 'page_number'
        if i == jsc.tag['page']:
            c = 'page_number_selected'
        
        html_pages += f"""<a class={c} href="" onclick="call_py('on_change_page_clicked', {i}); return false;">{i}</a>"""
    html_pages += '<div>'
    html += html_pages
    
    # display
    jsc['#div_data'].html = html


# --------------------------------------------------
#    Event Handlers
# --------------------------------------------------
def on_change_page_clicked(jsc, new_page_number):
    """ called when the prev, next, or a page number is clicked on the page selector at the bottom of the data table
    
        Args:
            jsc - javascript context
            new_page_number - the new page number to display    
    """
    # save the new page number
    if new_page_number == 'Prev':
        jsc.tag['page'] = jsc.tag['page'] - 1
    elif new_page_number == 'Next':
        jsc.tag['page'] = jsc.tag['page'] + 1
    else:
        jsc.tag['page'] = new_page_number
    
    jsc.tag['page'] = max(1, jsc.tag['page'])
    jsc.tag['page'] = min(jsc.tag['max_page'], jsc.tag['page'])

    # refresh the view        
    _refresh_view(jsc)


def on_delete_button_clicked(jsc, pk):
    """ called when the delete button for a record is clicked
        This will bring up a confirmation screen
    
        Args:
            jsc - javascript context
            pk - primary key of the record to delete    
    """
    jsc.modal_confirm('Confirm Delete', f'Are you sure you want to delete record with primary key of "{pk}"', f"""onclick="call_py('on_delete_confirm_button_clicked', '{pk}');" """)    


def on_delete_confirm_button_clicked(jsc, pk):
    """ called when the user has clicked through the confirmation screen for the delete.
        This will perform the actual delete
    
        Args:
            jsc - javascript context
            pk - primary key of the record to delete    
    """
    delete_record(jsc.tag['data_props'], pk)
    _refresh_view(jsc)
    

def on_edit_button_clicked(jsc, pk):
    """ called when the edit button for a record is clicked
    
        Args:
            jsc - javascript context
            pk - primary key of the record to edit    
    """
    # construct html to edit
    rd = get_record_for_updating(jsc.tag['data_props'], pk)

    # build the html for the body
    html = '<table>'
    html += f"""<tr><td>Primary Key</td><td id=pk>{rd['primary_key']['value']}</td></tr>"""    
    for i, r in enumerate(rd['records']):
        html += f"""<tr><td>{r['field_name']}</td><td><input id=input_{i} size=40 type=text value="{r['value']}"></td></tr>"""
    html += '</table>'
    
    # create the modal dialog first with autoshow set to False    
    jsc.modal_new('Edit Record',
                  html,
                  [{'text': 'Cancel', 'classes': 'btn-secondary', 'attributes': 'data-bs-dismiss="modal"'},
                   {'text': 'OK', 'classes': 'btn-primary', 'attributes': """data-bs-dismiss="modal"; onclick=call_py("on_edit_button_ok_clicked");"""}],
                   autoshow=False)

    # show the dialog after modification
    jsc.modal_show()    


def on_edit_button_ok_clicked(jsc):
    pk = jsc['#pk'].html
    rd = get_record_for_updating(jsc.tag['data_props'], pk)
    
    for i in range(0, len(rd['records'])):
        value = jsc.eval_js_code(f"""$("#input_{i}").val()""")
        rd['records'][i]['value'] = value
    
    update_record(jsc.tag['data_props'], rd)    
    _refresh_view(jsc)
    jsc.modal_alert('Record Updated', 'Record has been updated')


def on_header_clicked(jsc, header_index):
    """ called when the header at the top of the table is clicked
        This will resort the data by the column clicked
    
        Args:
            jsc - javascript context
            header_index - column number to restort the data by, 0 is the index, 1 is the first data column    
    """
    resort_data(jsc.tag['data_props'], header_index)
    _refresh_view(jsc) 


def ready(jsc, *args):
    """ called when a webpage creates a new connection the first time on load """
    jsc.tag['data_props'] = {}
    init_data(jsc.tag['data_props'] )    
    jsc.tag['page'] = 1
    jsc.tag['records_per_page'] = 25
    jsc.tag['max_page'] = math.ceil(get_record_count(jsc.tag['data_props']) / jsc.tag['records_per_page'])
    _refresh_view(jsc)


def reconnect(jsc, *args):
    """ called when a webpage automatically reconnects a broken connection """
    # reload if we lose web connection
    ready(jsc, *args)


# --------------------------------------------------
#   Main
# --------------------------------------------------
def main(args):
    # start the thread and the app
    args['port'] = args.get('port', 8300)
    logging.basicConfig(level=logging.DEBUG, format='%(relativeCreated)6d %(threadName)s %(message)s')
    run_pylinkjs_app(default_html='crud_app.html', html_dir=os.path.dirname(__file__), internal_polling_interval=0.025, port=args['port'])

if __name__ == '__main__':
    main()
