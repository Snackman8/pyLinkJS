"""
This demo was created by pasting the pyLinkJS README into ChatGPT-5o
(see: https://github.com/Snackman8/pyLinkJS/edit/master/README.md)
and then providing the following prompt:

   Demo Prompt
   ------------
   I’m using the pyLinkJS package. Please create the smallest working example
   app, based on the skeleton style, that does the following:

   • The HTML loads Plotly.js via CDN.
   • The page has a button and an empty <div> for a chart.
   • When the button is clicked, it calls a Python function using call_py.
   • The Python function generates 10 random integers between 0 and 100,
     then sends them back to the browser with jsc.eval_js_code.
   • The browser uses Plotly to draw a line chart of those numbers.
   • Provide two files: plotly_demo.py and plotly_demo.html.
   • Keep the code minimal and copy-paste runnable.

To run this demo:
1. Save the two files as plotly_demo.py and plotly_demo.html
   in the same directory.
2. Start the app with:
      python3 plotly_demo.py
3. Open your browser to:
      http://localhost:8300
"""

import argparse
import logging
import random
from pylinkjs.PyLinkJS import run_pylinkjs_app

def gen_data(jsc):
    # generate 10 random numbers
    numbers = [random.randint(0, 100) for _ in range(10)]
    # send them back to browser and plot with Plotly
    jsc.eval_js_code(f"""
        Plotly.newPlot('chart', [{{
            y: {numbers},
            type: 'scatter',
            mode: 'lines+markers'
        }}]);
    """)

parser = argparse.ArgumentParser()
parser.add_argument('--port', type=int, default=8300)
args = parser.parse_args()

logging.basicConfig(level=logging.DEBUG,
                    format='%(relativeCreated)6d %(threadName)s %(message)s')

run_pylinkjs_app(default_html='plotly_demo.html', port=args.port)
