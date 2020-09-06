<script>
    var ws;
    
    // Add the pylinkjs websocket handlers
    document.addEventListener("DOMContentLoaded", function(){
        // create the new websocket
        ws = new WebSocket("ws://" + location.host + "/websocket/" + Math.random());
        
        // open handler
        ws.onopen = function() {
            call_py('ready');
        };
        
        ws.onmessage = function (evt) {
            d = JSON.parse(evt.data);
            if (d['cmd'] == 'eval_js') {
                retval = eval(d['js_code']);
                if (!d['no_wait']) {
                    call_py('js_return_value', d['id'], retval);
                } 
            }
        };
    });
    
    function call_py(py_func_name, ...args) {
        // use the websocket to proxy the function call to python
        console.log('callpy');
        pkt = {'id': 'js_' + Math.random(),
               'cmd': 'call_py',
               'py_func_name': py_func_name,
               'args': args}
        ws.send(JSON.stringify(pkt));
    }
</script>