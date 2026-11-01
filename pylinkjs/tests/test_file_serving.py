import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application, RequestHandler

from pylinkjs.PyLinkJS import DEFAULT_SERVABLE_FILE_REGEX, MainHandler, run_pylinkjs_app


class CustomHandler(RequestHandler):
    def get(self):
        self.write('custom route')


class FileServingTests(AsyncHTTPTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'public'
        self.root.mkdir()
        self.on_404 = Mock(return_value=('dynamic response', 'text/plain', 200))
        super().setUp()

    def get_app(self):
        return Application(
            [(r'/api', CustomHandler), (r'/.*', MainHandler)],
            html_dir=str(self.root), default_html='index.html', plugins=[],
            servable_file_regex=re.compile(DEFAULT_SERVABLE_FILE_REGEX),
            on_404=self.on_404, extra_settings={},
        )

    def write_file(self, name, content=b'public asset'):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    def test_default_allows_assets_in_subdirectories_and_ignores_case(self):
        for extension in ('css', 'js', 'mjs', 'png', 'jpg', 'jpeg', 'gif', 'svg', 'webp',
                          'avif', 'ico', 'bmp', 'woff', 'woff2', 'ttf', 'otf', 'eot'):
            with self.subTest(extension=extension):
                name = 'assets/test.' + extension.upper()
                self.write_file(name)
                response = self.fetch('/' + name)
                self.assertEqual(response.code, 200)
                self.assertEqual(response.body, b'public asset')

    def test_default_pages_and_uppercase_html_are_processed(self):
        for name, url in (('index.html', '/'), ('nested/index.html', '/nested/'),
                          ('PAGE.HTML', '/PAGE.HTML'), ('page.htm', '/page.htm')):
            with self.subTest(url=url):
                self.write_file(name, b'<p>public page</p>')
                response = self.fetch(url)
                self.assertEqual(response.code, 200)
                self.assertIn(b'<p>public page</p>', response.body)
                self.assertIn(b'call_py', response.body)

    def test_default_blocks_non_assets_without_reading_or_falling_through(self):
        for name in ('app.py', 'notes.txt', 'README.md', 'settings.json', 'config.yaml',
                     'config.ini', 'users.sqlite3', 'server.log', 'app.py.bak', 'image.png.py'):
            with self.subTest(name=name):
                self.write_file(name, b'private data')
                with patch('builtins.open', side_effect=AssertionError('must not read rejected files')):
                    response = self.fetch('/' + name)
                self.assertEqual(response.code, 404)
        self.on_404.assert_not_called()

    def test_rejected_file_does_not_start_print_rendering(self):
        self.write_file('app.py')
        with patch('pylinkjs.PyLinkJS.threading') as threads:
            self.assertEqual(self.fetch('/app.py?output=pdf').code, 404)
        threads.Thread.assert_not_called()

    def test_override_allows_only_a_specific_python_file_and_replaces_default(self):
        self._app.settings['servable_file_regex'] = re.compile(r'downloads/example\.py')
        for name in ('downloads/example.py', 'other/example.py', 'downloads/example.py.bak',
                     'downloads/EXAMPLE.py', 'style.css'):
            self.write_file(name)
            expected = 200 if name == 'downloads/example.py' else 404
            self.assertEqual(self.fetch('/' + name).code, expected)

    def test_documented_override_extends_default_assets(self):
        self._app.settings['servable_file_regex'] = re.compile(
            DEFAULT_SERVABLE_FILE_REGEX + r'|downloads/example\.py')
        for name in ('downloads/example.py', 'style.CSS', 'other.py'):
            self.write_file(name)
            response = self.fetch('/' + name)
            self.assertEqual(response.code, 404 if name == 'other.py' else 200)

    def test_hidden_paths_and_symlinks_are_blocked_even_with_broad_override(self):
        self._app.settings['servable_file_regex'] = re.compile(r'.*')
        for name in ('.env', '.git/config', '.hidden/image.png', 'assets/.secret.png'):
            self.write_file(name)
            self.assertEqual(self.fetch('/' + name).code, 404)
        source = self.write_file('app.py')
        outside = Path(self.temp.name) / 'outside.png'
        outside.write_bytes(b'outside secret')
        (self.root / 'source.png').symlink_to(source)
        (self.root / 'outside.png').symlink_to(outside)
        (self.root / 'linked').symlink_to(outside.parent, target_is_directory=True)
        (self.root / 'broken.png').symlink_to(self.root / 'missing.png')
        for url in ('/source.png', '/outside.png', '/linked/outside.png', '/broken.png'):
            self.assertEqual(self.fetch(url).code, 404)
        self.on_404.assert_not_called()

    def test_directory_default_is_checked(self):
        self.write_file('app.py')
        self._app.settings['default_html'] = 'app.py'
        self.assertEqual(self.fetch('/').code, 404)
        self._app.settings['default_html'] = '../outside.png'
        self.assertEqual(self.fetch('/').code, 404)

    def test_path_traversal_is_blocked(self):
        self.assertEqual(self.fetch('/../outside.png').code, 403)

    def test_missing_paths_posts_and_custom_routes_still_work(self):
        for url in ('/generated', '/missing.txt'):
            response = self.fetch(url)
            self.assertEqual(response.code, 200)
            self.assertEqual(response.body, b'dynamic response')
        response = self.fetch('/submit', method='POST', body='input')
        self.assertEqual(response.code, 200)
        self.assertEqual(response.body, b'dynamic response')
        self.assertEqual(self.fetch('/api').body, b'custom route')


class FileServingConfigurationTests(unittest.TestCase):
    def test_invalid_regex_fails_at_startup(self):
        with self.assertRaises(re.error):
            run_pylinkjs_app(servable_file_regex='[')


if __name__ == '__main__':
    unittest.main()
