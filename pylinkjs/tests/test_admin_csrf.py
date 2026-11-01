from html.parser import HTMLParser
from http.cookies import SimpleCookie
import tempfile
import unittest
from urllib.parse import urlencode

from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application, create_signed_value

from pylinkjs.PyLinkJS import MainHandler
from pylinkjs.plugins.authLocalAuthAdminPlugin import pluginLocalAuthAdmin
from pylinkjs.plugins.authLocalAuthPlugin import (
    create_local_auth_user, get_local_auth_user, list_local_auth_users, pluginLocalAuth,
)


class AdminForms(HTMLParser):
    def __init__(self, body):
        super().__init__()
        self.forms = []
        self.current = None
        self.feed(body.decode())

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'form':
            self.current = {'action': attrs.get('action'), 'fields': {}}
            self.forms.append(self.current)
        elif tag == 'input' and self.current is not None and attrs.get('name'):
            self.current['fields'][attrs['name']] = attrs.get('value', '')

    def handle_endtag(self, tag):
        if tag == 'form':
            self.current = None


class AdminCSRFTests(AsyncHTTPTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = self.temp.name + '/users.sqlite3'
        self.auth = pluginLocalAuth(self.db)
        super().setUp()

    def get_app(self):
        settings = dict(
            cookie_secret='fixture-secret', require_auth=True,
            cookiename_user_auth_username='fixture_username',
            cookiename_user_auth_method='fixture_method', extra_settings={},
            auth_cookie_options={'secure': False, 'httponly': True, 'samesite': 'Lax'},
            on_404=lambda *args: ('application POST response', 'text/plain', 200),
        )
        self.auth.register(settings)
        pluginLocalAuthAdmin(self.db).register(settings)
        routes = settings.pop('route_handlers')
        return Application(routes + [(r'/.*', MainHandler)], **settings)

    def auth_cookie(self, username):
        value = create_signed_value('fixture-secret', 'fixture_username', username).decode()
        return 'fixture_username=' + value

    def admin_page(self):
        if get_local_auth_user(self.db, 'admin') is None:
            create_local_auth_user(self.db, 'admin', 'fixture-password', is_admin=True)
        return self.form_page('/admin/users', self.auth_cookie('admin'))

    def form_page(self, url, auth_cookie=''):
        response = self.fetch(url, headers={'Cookie': auth_cookie})
        self.assertEqual(response.code, 200)
        cookies = SimpleCookie()
        cookies.load(auth_cookie)
        for header in response.headers.get_list('Set-Cookie'):
            cookies.load(header)
        forms = AdminForms(response.body).forms
        self.assertTrue(forms)
        self.assertIn('_xsrf', cookies)
        for form in forms:
            self.assertTrue(form['fields'].get('_xsrf'))
        return cookies, forms

    def submit(self, url, fields, cookies, headers=None):
        request_headers = dict(headers or {})
        request_headers['Cookie'] = '; '.join(f'{name}={value.coded_value}' for name, value in cookies.items())
        return self.fetch(url, method='POST', follow_redirects=False,
                          headers=request_headers, body=urlencode(fields))

    def test_all_create_and_delete_forms_include_tokens(self):
        create_local_auth_user(self.db, 'member', 'fixture-password')
        _, forms = self.admin_page()
        self.assertEqual([form['action'] for form in forms].count('/admin/users/create'), 1)
        self.assertEqual([form['action'] for form in forms].count('/admin/users/delete'), 2)

    def test_rejected_admin_submissions_leave_users_unchanged(self):
        create_local_auth_user(self.db, 'member', 'fixture-password')
        cookies, forms = self.admin_page()
        _, other_forms = self.admin_page()
        token = forms[0]['fields']['_xsrf']
        other_token = other_forms[0]['fields']['_xsrf']
        before = list_local_auth_users(self.db)
        for url, fields in (
            ('/admin/users/create', {'username': 'forged-admin', 'password': 'fixture-password', 'is_admin': '1'}),
            ('/admin/users/delete', {'username': 'member'}),
        ):
            for supplied_token in (None, 'invalid-token', other_token):
                with self.subTest(url=url, token=supplied_token):
                    body = dict(fields)
                    if supplied_token is not None:
                        body['_xsrf'] = supplied_token
                    response = self.submit(url, body, cookies, headers={'Origin': 'https://other.example.test'})
                    self.assertEqual(response.code, 403)
                    self.assertEqual(list_local_auth_users(self.db), before)
            # A form token also needs its corresponding cookie.
            response = self.submit(url, dict(fields, _xsrf=token), SimpleCookie(self.auth_cookie('admin')))
            self.assertEqual(response.code, 403)
            self.assertEqual(list_local_auth_users(self.db), before)

    def test_valid_create_and_delete_forms_work(self):
        cookies, forms = self.admin_page()
        token = forms[0]['fields']['_xsrf']
        response = self.submit('/admin/users/create', {
            'username': 'new-member', 'password': 'fixture-password', '_xsrf': token,
        }, cookies)
        self.assertEqual(response.code, 302)
        self.assertIsNotNone(get_local_auth_user(self.db, 'new-member'))
        response = self.submit('/admin/users/delete', {'username': 'new-member', '_xsrf': token}, cookies)
        self.assertEqual(response.code, 302)
        self.assertIsNone(get_local_auth_user(self.db, 'new-member'))

    def test_scripts_can_send_token_in_header(self):
        cookies, forms = self.admin_page()
        response = self.submit('/admin/users/create', {
            'username': 'script-created', 'password': 'fixture-password',
        }, cookies, headers={'X-XSRFToken': forms[0]['fields']['_xsrf']})
        self.assertEqual(response.code, 302)
        self.assertIsNotNone(get_local_auth_user(self.db, 'script-created'))

    def test_valid_token_does_not_bypass_admin_authorization(self):
        cookies, forms = self.admin_page()
        create_local_auth_user(self.db, 'member', 'fixture-password')
        cookies.load(self.auth_cookie('member'))
        response = self.submit('/admin/users/create', {
            'username': 'unauthorized', 'password': 'fixture-password',
            '_xsrf': forms[0]['fields']['_xsrf'],
        }, cookies)
        self.assertEqual(response.code, 403)
        self.assertIsNone(get_local_auth_user(self.db, 'unauthorized'))

    def test_bootstrap_rejects_forgery_and_accepts_its_form_token(self):
        cookies, forms = self.form_page('/admin/users/bootstrap')
        self.assertEqual(forms[0]['action'], '/admin/users/bootstrap')
        for fields in ({}, {'_xsrf': 'invalid-token'}):
            response = self.submit('/admin/users/bootstrap', dict(
                username='first-admin', password='fixture-password', **fields), cookies)
            self.assertEqual(response.code, 403)
            self.assertEqual(list_local_auth_users(self.db), [])
        response = self.submit('/admin/users/bootstrap', {
            'username': 'first-admin', 'password': 'fixture-password',
            '_xsrf': forms[0]['fields']['_xsrf'],
        }, cookies)
        self.assertEqual(response.code, 302)
        self.assertTrue(get_local_auth_user(self.db, 'first-admin')['is_admin'])

    def test_application_posts_do_not_require_admin_csrf_tokens(self):
        cookies, _ = self.admin_page()
        response = self.submit('/application-api', {'value': 'fixture'}, cookies)
        self.assertEqual(response.code, 200)
        self.assertEqual(response.body, b'application POST response')
        self.assertFalse(self._app.settings.get('xsrf_cookies', False))


if __name__ == '__main__':
    unittest.main()
