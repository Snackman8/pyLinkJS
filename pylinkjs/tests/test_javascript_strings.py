import json
import subprocess
import unittest
from unittest.mock import Mock

from playwright._impl._driver import compute_driver_executable

from pylinkjs.PyLinkJS import Code, PyLinkHTMLElementWrapper


class JavaScriptStringTests(unittest.TestCase):
    def setUp(self):
        self.client = Mock()
        self.element = PyLinkHTMLElementWrapper(self.client, '#output')

    def evaluate_updates(self):
        # Use Playwright's bundled Node runtime; no browser or network is needed.
        node, _ = compute_driver_executable()
        script = r"""
            const calls = [];
            globalThis.$ = selector => new Proxy({}, {
                get: (_, method) => (...args) => calls.push({selector, method, args})
            });
            eval(require('fs').readFileSync(0, 'utf8'));
            for (const call of calls) {
                call.args = call.args.map(value => typeof value === 'function'
                    ? {type: 'function', result: value()} : value);
            }
            console.log(JSON.stringify({calls, injected: !!globalThis.injected}));
        """
        updates = '\n'.join(call.args[0] for call in self.client.eval_js_code.call_args_list)
        result = subprocess.run([str(node), '-e', script], input=updates, text=True,
                                capture_output=True, timeout=5, check=True)
        return json.loads(result.stdout)

    def test_text_interpolation_is_not_executed(self):
        value = '${(globalThis.injected = true)}'
        self.element.text = value

        result = self.evaluate_updates()

        self.assertFalse(result['injected'])
        self.assertEqual(result['calls'][0]['args'], [value])

    def test_strings_remain_literal_through_element_css_and_prop_updates(self):
        values = [
            '', 'plain text', 'single \' and double " quotes', '`backticks`',
            '${(globalThis.injected = true)}',
            '`); globalThis.injected = true; //',
            '\\${(globalThis.injected = true)}',
            'line one\nline two\r\ttab\x00', r'C:\path\to\file',
            'Unicode: café ☃ \u2028 \u2029',
        ]
        targets = [(self.element, 'text'), (self.element, 'val'), (self.element, 'html'),
                   (self.element.css, 'color'), (self.element.prop, 'title')]
        for target, attribute in targets:
            with self.subTest(attribute=attribute):
                self.client.reset_mock()
                for value in values:
                    setattr(target, attribute, value)

                result = self.evaluate_updates()

                self.assertFalse(result['injected'])
                self.assertEqual([call['args'][-1] for call in result['calls']], values)

    def test_code_event_handler_remains_executable(self):
        self.element.click = Code('function() { globalThis.injected = true; return "clicked"; }')

        result = self.evaluate_updates()

        self.assertTrue(result['injected'])
        self.assertEqual(result['calls'][0]['method'], 'click')
        self.assertEqual(result['calls'][0]['args'], [{'type': 'function', 'result': 'clicked'}])

    def test_numeric_boolean_and_code_properties_keep_their_types(self):
        self.element.css.width = 12
        self.element.css.opacity = 0.5
        self.element.prop.disabled = True
        self.element.prop.hidden = False
        self.element.prop.title = Code('"explicit code"')

        result = self.evaluate_updates()

        self.assertFalse(result['injected'])
        self.assertEqual([call['args'][-1] for call in result['calls']],
                         [12, 0.5, True, False, 'explicit code'])


if __name__ == '__main__':
    unittest.main()
