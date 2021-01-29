<script>
    var ws;
    var pkt_id = 0;
    
    // Add the pylinkjs websocket handlers
    document.addEventListener("DOMContentLoaded", function(){
        // create the new websocket
        ws = new WebSocket("ws://" + location.host + "/websocket/" + Math.random());
        
        // open handler
        ws.onopen = function() {
            // synchronize watches
            pkt = {'id': 'js_' + pkt_id,
                   'cmd': 'synchronize_time',
                   'event_time_ms': new Date().getTime()}
            ws.send(JSON.stringify(pkt));
            pkt_id = pkt_id + 1
        
            if (!(typeof pylinkjs_ready === 'undefined')) {
                pylinkjs_ready();
            }
            
            call_py_optional('ready');
        };
        
        ws.onmessage = function (evt) {
            d = JSON.parse(evt.data);
            if (d['cmd'] == 'eval_js') {
                try {
                    retval = eval(d['js_code']);
                } catch (err) {
                    alert(err)
                    throw err
                }
                if (!d['no_wait']) {
                    call_py('js_return_value', d['id'], retval);
                } 
            }
        };
    });

    function call_py(py_func_name, ...args) {
        /** call call_py_ex but throw error if the py_func_name is not defined **/
        call_py_ex(py_func_name, new Boolean(0), ...args);
    }

    function call_py_ex(py_func_name, no_error_if_undefined, ...args) {
        // use the websocket to proxy the function call to python
        pkt = {'id': 'js_' + pkt_id,
               'cmd': 'call_py',
               'py_func_name': py_func_name,
               'args': args,
               'event_time_ms': new Date().getTime(),
               'no_error_if_undefined': no_error_if_undefined}
        ws.send(JSON.stringify(pkt));
        pkt_id = pkt_id + 1        
    }

    function call_py_optional(py_func_name, ...args) {
        /** call call_py_ex but no error if the py_func_name is not defined **/
        call_py_ex(py_func_name, new Boolean(1), ...args);
    }
</script>