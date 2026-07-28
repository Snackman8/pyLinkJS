import types
import threading
import unittest

from pylinkjs.PyLinkJS import (
    PyLinkJSCallback,
    PyLinkJSWebSocketHandler,
    _run_background_callback,
    _normalize_callback_registry,
    run_pylinkjs_app,
    set_auth_cookie,
)


def example_callback(_jsc):
    pass


class CookieHandler:
    def __init__(self):
        self.application = types.SimpleNamespace(settings={
            'auth_cookie_options': {'secure': True, 'httponly': True, 'samesite': 'Lax'},
        })
        self.calls = []

    def set_secure_cookie(self, name, value, **kwargs):
        self.calls.append((name, value, kwargs))


class HighSecurityRegistryTests(unittest.TestCase):
    def test_registry_wraps_plain_callables_and_preserves_thread_permission(self):
        registry = _normalize_callback_registry({
            '/': {
                'ready': example_callback,
                'generate_report': PyLinkJSCallback(example_callback, allow_new_thread=True),
            },
        })

        self.assertIs(registry['/']['ready'].func, example_callback)
        self.assertFalse(registry['/']['ready'].allow_new_thread)
        self.assertTrue(registry['/']['generate_report'].allow_new_thread)

    def test_registry_rejects_missing_or_unsafe_entries(self):
        with self.assertRaises(ValueError):
            _normalize_callback_registry(None)
        with self.assertRaises(ValueError):
            _normalize_callback_registry({'relative-path': {'ready': example_callback}})
        with self.assertRaises(ValueError):
            _normalize_callback_registry({'/': {'not.a.callback': example_callback}})
        with self.assertRaises(TypeError):
            _normalize_callback_registry({'/': {'ready': 'not callable'}})

    def test_websocket_route_is_derived_from_the_endpoint(self):
        handler = object.__new__(PyLinkJSWebSocketHandler)
        handler.request = types.SimpleNamespace(path='/websocket/0.example/reports/view.html')

        self.assertEqual(handler._get_websocket_route(), ('0.example', '/reports/view.html'))

    def test_background_callback_releases_its_slot(self):
        slots = threading.BoundedSemaphore(1)
        self.assertTrue(slots.acquire(blocking=False))
        _run_background_callback(PyLinkJSCallback(example_callback), None, [], slots)
        self.assertTrue(slots.acquire(blocking=False))
        slots.release()

    def test_high_security_rejects_the_example_cookie_secret(self):
        with self.assertRaisesRegex(ValueError, 'cannot be used with the example cookie_secret'):
            run_pylinkjs_app(
                high_security=True,
                cookie_secret='CHANGEME',
                callback_registry={'/': {'ready': example_callback}},
            )

    def test_auth_cookie_uses_the_application_cookie_policy(self):
        handler = CookieHandler()
        set_auth_cookie(handler, 'session', 'value')

        self.assertEqual(handler.calls, [
            ('session', 'value', {'secure': True, 'httponly': True, 'samesite': 'Lax'}),
        ])


if __name__ == '__main__':
    unittest.main()
