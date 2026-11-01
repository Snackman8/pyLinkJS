import asyncio
from pathlib import Path
import re
import tempfile
import threading
import unittest
from unittest.mock import MagicMock, Mock, call, patch
from urllib.parse import parse_qs, urlencode, urlsplit

from playwright.sync_api import Browser, Error as PlaywrightError
from tornado.testing import AsyncHTTPTestCase, gen_test
from tornado.web import Application

from pylinkjs.PyLinkJS import (
    DEFAULT_SERVABLE_FILE_REGEX, DEFAULT_PRINT_ALLOWED_ORIGINS, MainHandler,
    _restrict_print_requests, print_url, run_pylinkjs_app,
)


class PrintRequestTests(AsyncHTTPTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        (Path(self.temp.name) / 'index.html').write_text('<p>print fixture</p>')
        super().setUp()

    def get_app(self):
        return Application([(r'/.*', MainHandler)], html_dir=self.temp.name,
                           default_html='index.html',
                           servable_file_regex=re.compile(DEFAULT_SERVABLE_FILE_REGEX),
                           print_job_slots=threading.BoundedSemaphore(2), port=8300,
                           print_allowed_origins=DEFAULT_PRINT_ALLOWED_ORIGINS)

    @gen_test
    async def test_busy_requests_are_rejected_without_starting_another_job(self):
        loop = asyncio.get_running_loop()
        started = asyncio.Queue()
        release = threading.Event()

        def render(**kwargs):
            loop.call_soon_threadsafe(started.put_nowait, True)
            if not release.wait(5):
                raise RuntimeError('test did not release rendering job')
            return b'fixture-pdf', 'application/pdf'

        jobs = []
        with patch('pylinkjs.PyLinkJS.print_url', side_effect=render) as renderer:
            try:
                for _ in range(2):
                    jobs.append(self.http_client.fetch(self.get_url('/?output=pdf')))
                    await asyncio.wait_for(started.get(), timeout=2)
                response = await self.http_client.fetch(self.get_url('/?output=pdf'), raise_error=False)
                self.assertEqual(response.code, 503)
                self.assertEqual(renderer.call_count, 2)
            finally:
                release.set()
                responses = await asyncio.gather(*jobs)
            self.assertTrue(all(response.body == b'fixture-pdf' for response in responses))
            response = await self.http_client.fetch(self.get_url('/?output=pdf'))
            self.assertEqual(response.code, 200)

    def test_failed_job_releases_its_slot(self):
        self._app.settings['print_job_slots'] = threading.BoundedSemaphore(1)
        with patch('pylinkjs.PyLinkJS.print_url', side_effect=[
                RuntimeError('fixture failure'), (b'fixture-pdf', 'application/pdf')]):
            self.assertEqual(self.fetch('/?output=pdf').code, 500)
            self.assertEqual(self.fetch('/?output=pdf').body, b'fixture-pdf')

    def test_executor_failure_releases_its_slot(self):
        self._app.settings['print_job_slots'] = threading.BoundedSemaphore(1)
        with patch.object(self.io_loop, 'run_in_executor', side_effect=RuntimeError('fixture failure')):
            self.assertEqual(self.fetch('/?output=pdf').code, 500)
        with patch('pylinkjs.PyLinkJS.print_url', return_value=(b'fixture-pdf', 'application/pdf')):
            self.assertEqual(self.fetch('/?output=pdf').code, 200)

    def test_invalid_waits_are_rejected_before_rendering(self):
        with patch('pylinkjs.PyLinkJS.print_url') as renderer:
            for name in ('print_timeout', 'print_extra_delay'):
                for value in ('-1', 'nan', 'inf', '-inf', 'invalid', ''):
                    with self.subTest(name=name, value=value):
                        response = self.fetch('/?' + urlencode({'output': 'pdf', name: value}))
                        self.assertEqual(response.code, 400)
            self.assertEqual(self.fetch('/?output=pdf&print_timeout=%FF').code, 400)
            renderer.assert_not_called()

    def test_large_waits_are_capped_and_png_still_works(self):
        with patch('pylinkjs.PyLinkJS.print_url', return_value=(b'fixture-png', 'image/png')) as renderer:
            response = self.fetch('/?output=png&print_timeout=999999&print_extra_delay=999999')
            self.assertEqual(response.code, 200)
            self.assertEqual(response.body, b'fixture-png')
            self.assertEqual(response.headers['Content-Type'], 'image/png')
            self.assertEqual(renderer.call_args.kwargs['output_type'], 'png')
            self.assertEqual(renderer.call_args.kwargs['timeout'], 60)
            self.assertEqual(renderer.call_args.kwargs['extra_delay'], 10)

    def test_print_url_ignores_host_headers_and_preserves_page_query(self):
        with patch('pylinkjs.PyLinkJS.print_url', return_value=(b'fixture-pdf', 'application/pdf')) as renderer:
            response = self.fetch('/?output=pdf&item=output%3Dpdf&item=two%20words&print_timeout=1',
                                  headers={'Host': '169.254.169.254', 'X-Forwarded-Host': 'evil.example',
                                           'X-Forwarded-Proto': 'https'})
            self.assertEqual(response.code, 200)
            destination = urlsplit(renderer.call_args.kwargs['url'])
            self.assertEqual((destination.scheme, destination.netloc, destination.path),
                             ('http', '127.0.0.1:8300', '/'))
            self.assertEqual(parse_qs(destination.query), {'item': ['output=pdf', 'two words']})
            self.assertEqual(renderer.call_args.kwargs['allowed_origins'], DEFAULT_PRINT_ALLOWED_ORIGINS)


class PrintRendererTests(unittest.TestCase):
    def setUp(self):
        self.playwright_patch = patch('pylinkjs.PyLinkJS.sync_playwright')
        self.playwright = self.playwright_patch.start().return_value.__enter__.return_value
        self.addCleanup(self.playwright_patch.stop)
        self.browser = MagicMock()
        self.browser.__enter__.return_value = self.browser
        # Exercise Playwright's real context-manager cleanup without launching Chromium.
        self.browser.__exit__.side_effect = lambda *args: Browser.__exit__(self.browser, *args)
        self.playwright.chromium.launch.return_value = self.browser
        self.page = self.browser.new_page.return_value
        self.page.screenshot.return_value = b'fixture-png'
        self.page.pdf.return_value = b'fixture-pdf'

    def test_pdf_and_png_close_browser_on_success(self):
        for output in ('pdf', 'png'):
            with self.subTest(output=output):
                self.browser.close.reset_mock()
                result, _ = print_url('http://localhost/', output, timeout=0, extra_delay=0)
                self.assertEqual(result, b'fixture-' + output.encode())
                self.browser.close.assert_called_once()
                self.playwright.chromium.launch.assert_called_with(timeout=30000)
                self.page.set_default_timeout.assert_called_with(30000)

    def test_navigation_timeout_closes_browser(self):
        self.page.goto.side_effect = PlaywrightError('fixture navigation timeout')
        with self.assertRaisesRegex(RuntimeError, 'fixture navigation timeout'):
            print_url('http://localhost/', 'pdf', timeout=0)
        self.browser.close.assert_called_once()

    def test_screenshot_failure_closes_browser(self):
        self.page.screenshot.side_effect = PlaywrightError('fixture screenshot failure')
        with self.assertRaises(RuntimeError):
            print_url('http://localhost/', 'png', timeout=0)
        self.browser.close.assert_called_once()

    def test_page_hint_and_explicit_waits_are_capped(self):
        for timeout in (None, 999999):
            with self.subTest(timeout=timeout), \
                    patch('pylinkjs.PyLinkJS.time.monotonic', side_effect=[0, 59, 61]):
                self.page.wait_for_timeout.reset_mock()
                self.page.evaluate.side_effect = lambda code: 999999 if 'HINT_PRINT_TIMEOUT' in code else 0
                result, _ = print_url('http://localhost/', 'png', timeout=timeout, extra_delay=999999)
                self.assertEqual(result, b'fixture-png')
                self.assertEqual(self.page.wait_for_timeout.call_args_list, [call(1000), call(10000)])

    def test_invalid_page_hint_uses_default_wait(self):
        self.page.evaluate.side_effect = lambda code: float('nan') if 'HINT_PRINT_TIMEOUT' in code else 0
        with patch('pylinkjs.PyLinkJS.time.monotonic', side_effect=[0, 9, 11]):
            self.assertEqual(print_url('http://localhost/', 'png', extra_delay=0)[0], b'fixture-png')
        self.assertEqual(self.page.wait_for_timeout.call_args_list, [call(1000), call(0)])

    def test_invalid_direct_arguments_do_not_launch_browser(self):
        for arguments in ({'timeout': float('inf')}, {'extra_delay': -1}):
            with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                print_url('http://localhost/', 'pdf', **arguments)
        self.playwright.chromium.launch.assert_not_called()

    def test_invalid_concurrency_limit_fails_at_startup(self):
        for value in (0, -1, True, '2', 1.5, None):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'max_print_jobs'):
                run_pylinkjs_app(max_print_jobs=value)

    def test_http_print_context_blocks_service_workers_and_installs_routes_before_page(self):
        context = self.browser.new_context.return_value

        def new_page():
            context.route.assert_called_once()
            context.route_web_socket.assert_called_once()
            return self.page

        context.new_page.side_effect = new_page
        result, _ = print_url('http://127.0.0.1:8300/', 'pdf', timeout=0,
                              allowed_origins=DEFAULT_PRINT_ALLOWED_ORIGINS)
        self.assertEqual(result, b'fixture-pdf')
        self.browser.new_context.assert_called_once_with(service_workers='block')
        self.browser.close.assert_called_once()

    def test_invalid_asset_origin_configuration_fails_at_startup(self):
        for value in (None, 'https://cdn.example', ['file:///tmp'], ['https://cdn.example/path'],
                      ['https://cdn.example/?query=1'], ['https://user@cdn.example'],
                      ['http://[invalid'], [3]):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'print_allowed_origins'):
                run_pylinkjs_app(print_allowed_origins=value)


class PrintNetworkPolicyTests(unittest.TestCase):
    def setUp(self):
        context = Mock()
        _restrict_print_requests(context, 'http://127.0.0.1:8300/',
                                 [*DEFAULT_PRINT_ALLOWED_ORIGINS, 'https://cdn.plot.ly'])
        self.handle_request = context.route.call_args.args[1]
        self.block_websocket = context.route_web_socket.call_args.args[0]
        self.handle_websocket = context.route_web_socket.call_args.args[1]

    def route(self, url, navigation=False, status=200):
        route = Mock()
        route.request.url = url
        route.request.is_navigation_request.return_value = navigation
        route.fetch.return_value.status = status
        self.handle_request(route)
        return route

    def test_app_pages_and_approved_asset_origins_are_allowed(self):
        for url, navigation in [('http://127.0.0.1:8300/index.html', True),
                                ('http://127.0.0.1:8300/api', False),
                                ('https://cdn.jsdelivr.net:443/jquery.js', False),
                                ('https://cdn.plot.ly/plotly.js', False)]:
            with self.subTest(url=url):
                route = self.route(url, navigation)
                route.fetch.assert_called_once_with(max_redirects=0, timeout=30000)
                route.fulfill.assert_called_once_with(response=route.fetch.return_value)
                route.fetch.return_value.dispose.assert_called_once()
                route.abort.assert_not_called()

    def test_unapproved_destinations_are_blocked_before_network_fetch(self):
        for url in ('http://169.254.169.254/latest/', 'http://127.0.0.1:54321/private',
                    'https://evil.example/', 'https://cdn.jsdelivr.net.evil.example/',
                    'https://user@cdn.jsdelivr.net/private', 'file:///etc/passwd'):
            with self.subTest(url=url):
                route = self.route(url)
                route.abort.assert_called_once()
                route.fetch.assert_not_called()

    def test_navigation_cannot_leave_app_even_for_approved_asset_origins(self):
        route = self.route('https://cdn.jsdelivr.net/page.html', navigation=True)
        route.abort.assert_called_once()
        route.fetch.assert_not_called()

    def test_redirects_are_never_followed_or_passed_to_chromium(self):
        for status in (301, 302, 303, 307, 308):
            with self.subTest(status=status):
                route = self.route('http://127.0.0.1:8300/redirect', navigation=True, status=status)
                route.fetch.assert_called_once_with(max_redirects=0, timeout=30000)
                route.abort.assert_called_once()
                route.fulfill.assert_not_called()
                route.fetch.return_value.dispose.assert_called_once()

    def test_only_app_websockets_are_connected(self):
        for url, allowed in [('ws://127.0.0.1:8300/websocket/client/', True),
                             ('ws://127.0.0.1:54321/', False),
                             ('wss://cdn.jsdelivr.net/socket', False),
                             ('ws://evil.example/', False)]:
            with self.subTest(url=url):
                socket = Mock(url=url)
                self.assertEqual(self.block_websocket(url), not allowed)
                if self.block_websocket(url):
                    self.handle_websocket(socket)
                if allowed:
                    socket.close.assert_not_called()
                else:
                    socket.connect_to_server.assert_not_called()


if __name__ == '__main__':
    unittest.main()
