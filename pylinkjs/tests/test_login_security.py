from html.parser import HTMLParser
from http.cookies import SimpleCookie
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch
from urllib.parse import urlencode

from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application, create_signed_value, decode_signed_value

from pylinkjs.PyLinkJS import LoginHandler, _safe_next_url
from pylinkjs.plugins.authDevAuthPlugin import DevAuthLoginHandler
from pylinkjs.plugins.authLocalAuthPlugin import create_local_auth_user, pluginLocalAuth

# These tests exercise redirects and rendering, without LDAP or OAuth services.
with patch.dict(sys.modules, {'ldap': Mock(), 'ldap.filter': Mock(), 'requests': Mock()}):
    from pylinkjs.plugins.authLDAPAuthPlugin import LDAPAuthLoginHandler
    from pylinkjs.plugins.authGoogleOAuth2Plugin import GoogleOAuth2LoginHandler


class LoginPage(HTMLParser):
    def __init__(self, body):
        super().__init__()
        self.next_fields = []
        self.injected_tags = []
        self.feed(body.decode())

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'input' and attrs.get('name') == 'next':
            self.next_fields.append(attrs)
        if attrs.get('id') == 'injected':
            self.injected_tags.append(tag)


class ErrorLoginHandler(LoginHandler):
    def get(self):
        self._render_login(self.get_argument('error', ''))


class FailedLDAPLoginHandler(LDAPAuthLoginHandler):
    @classmethod
    def _check_ldap_login(cls, *args):
        return False


class StubOAuthLoginHandler(GoogleOAuth2LoginHandler):
    def authorize_redirect(self, **kwargs):
        self.redirect('https://accounts.example.invalid/')

    async def get_authenticated_user(self, **kwargs):
        return {'access_token': 'fixture-token'}

    async def oauth2_request(self, *args, **kwargs):
        return {'name': 'Fixture User', 'email': 'fixture@example.invalid'}


class LoginSecurityTests(AsyncHTTPTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = self.temp.name + '/users.sqlite3'
        self.local_auth = pluginLocalAuth(self.db)
        create_local_auth_user(self.db, 'fixture-user', 'fixture-password')
        super().setUp()

    def get_app(self):
        settings = dict(
            high_security=True, cookie_secret='fixture-cookie-secret',
            cookiename_user_auth_username='fixture_username',
            cookiename_user_auth_method='fixture_method',
            cookiename_user_auth_email='fixture_email',
            cookiename_user_auth_access_token='fixture_token',
            auth_cookie_options={'secure': False, 'httponly': True, 'samesite': 'Lax'},
            ldap_server='fixture', ldap_base='fixture', ldap_group='fixture',
            google_oauth_redirect_uri='https://app.example.invalid/oauth',
            google_oauth={'key': 'fixture-client-id'},
        )
        self.local_auth.register(settings)
        return Application([
            (r'/login', settings['login_handler']),
            (r'/base-login', LoginHandler),
            (r'/error-login', ErrorLoginHandler),
            (r'/dev-login', DevAuthLoginHandler),
            (r'/ldap-login', FailedLDAPLoginHandler),
            (r'/oauth-login', StubOAuthLoginHandler),
        ], **settings)

    def post_login(self, next_url, password='fixture-password', path='/login'):
        return self.fetch(path, method='POST', follow_redirects=False, body=urlencode({
            'username': 'fixture-user', 'password': password, 'next': next_url,
        }))

    def assert_escaped_page(self, response, next_url):
        self.assertEqual(response.code, 200)
        page = LoginPage(response.body)
        self.assertEqual(page.injected_tags, [])
        self.assertEqual(page.next_fields, [{'type': 'hidden', 'name': 'next', 'value': next_url}])

    def test_local_get_and_failed_post_escape_next_attribute(self):
        for value in ('/\"><script id="injected">alert(1)</script>',
                      '/reports?q="quoted"&name=O\'Reilly&value=<tag>'):
            with self.subTest(value=value):
                self.assert_escaped_page(self.fetch('/login?' + urlencode({'next': value})), value)
                self.assert_escaped_page(self.post_login(value, password='wrong'), value)

    def test_base_and_ldap_renderers_escape_referer(self):
        value = '/\"><script id="injected">alert(1)</script>'
        self.assert_escaped_page(self.fetch('/base-login', headers={'Referer': value}), value)
        response = self.fetch('/ldap-login', method='POST',
                              headers={'Referer': value},
                              body=urlencode({'username': 'fixture-user', 'password': 'wrong'}))
        self.assert_escaped_page(response, value)

    def test_error_messages_are_escaped(self):
        error = '<script id="injected">alert(1)</script>'
        response = self.fetch('/error-login?' + urlencode({'error': error}))
        self.assert_escaped_page(response, '/')
        self.assertIn(b'&lt;script id=&quot;injected&quot;&gt;', response.body)

    def test_valid_local_redirects_are_preserved_after_login(self):
        for value in ('/', '/reports/view.html', '/reports/?q=a%20b&sort=desc#row-2'):
            with self.subTest(value=value):
                response = self.post_login(value)
                self.assertEqual(response.code, 302)
                self.assertEqual(response.headers['Location'], value)
                self.assertTrue(response.headers.get_list('Set-Cookie'))

    def test_external_ambiguous_and_control_character_redirects_fall_back(self):
        values = ('https://evil.example/', '//evil.example/', '///evil.example/',
                  '/\\evil.example/', '/path\\evil', 'javascript:alert(1)',
                  'relative/path', '', '/path\n//evil', '/path\r//evil',
                  '/path\t//evil', '/path\x7f//evil')
        for value in values:
            with self.subTest(value=value):
                response = self.post_login(value)
                self.assertEqual(response.code, 302)
                self.assertEqual(response.headers['Location'], '/')

    def test_validator_rejects_raw_null_bytes(self):
        # Tornado replaces NULs with spaces in get_argument, so check raw input here.
        self.assertEqual(_safe_next_url('/path\x00//evil'), '/')

    def test_shared_post_handler_validates_development_login_redirects(self):
        response = self.post_login('//evil.example/', path='/dev-login')
        self.assertEqual(response.code, 302)
        self.assertEqual(response.headers['Location'], '/')

    def test_unsafe_next_is_not_preserved_in_login_form(self):
        response = self.fetch('/login?' + urlencode({'next': '//evil.example/'}))
        self.assert_escaped_page(response, '/')

    def test_oauth_validates_next_before_storing_and_after_reading_cookie(self):
        for value, expected in (('/reports/?page=2', '/reports/?page=2'),
                                ('https://evil.example/', '/')):
            with self.subTest(value=value):
                response = self.fetch('/oauth-login?' + urlencode({'next': value}), follow_redirects=False)
                self.assertEqual(response.code, 302)
                cookies = SimpleCookie()
                for header in response.headers.get_list('Set-Cookie'):
                    cookies.load(header)
                secret = self._app.settings['cookie_secret']
                state = decode_signed_value(secret, 'pylinkjs_google_oauth_state',
                                            cookies['pylinkjs_google_oauth_state'].value).decode()
                stored_next = decode_signed_value(secret, 'pylinkjs_google_oauth_next',
                                                  cookies['pylinkjs_google_oauth_next'].value).decode()
                self.assertEqual(stored_next, expected)

                # Simulate a valid next cookie issued before redirect validation existed.
                cookies['pylinkjs_google_oauth_next'] = create_signed_value(
                    secret, 'pylinkjs_google_oauth_next', value).decode()
                response = self.fetch('/oauth-login?' + urlencode({'code': 'fixture-code', 'state': state}),
                                      headers={'Cookie': cookies.output(header='', sep=';').strip()},
                                      follow_redirects=False)
                self.assertEqual(response.code, 302)
                self.assertEqual(response.headers['Location'], expected)

    def test_oauth_still_rejects_missing_or_invalid_state(self):
        response = self.fetch('/oauth-login?code=fixture-code&state=wrong', follow_redirects=False)
        self.assertEqual(response.code, 403)


if __name__ == '__main__':
    unittest.main()
