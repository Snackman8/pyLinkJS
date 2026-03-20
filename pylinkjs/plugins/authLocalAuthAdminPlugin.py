# --------------------------------------------------
#    Imports
# --------------------------------------------------
import html
from urllib.parse import urlencode

import tornado.web

from pylinkjs.PyLinkJS import BaseHandler
from pylinkjs.plugins.authLocalAuthPlugin import create_local_auth_user, delete_local_auth_user, get_local_auth_user, get_local_auth_user_count, list_local_auth_users


# --------------------------------------------------
#    Handler Helpers
# --------------------------------------------------
class _LocalAuthAdminBaseHandler(BaseHandler):
    def initialize(self, db_path, base_url='/admin/users'):
        self._db_path = db_path
        self._base_url = base_url.rstrip('/')
        self._bootstrap_url = self._base_url + '/bootstrap'

    def prepare(self):
        if get_local_auth_user_count(self._db_path) == 0:
            if self.request.path != self._bootstrap_url:
                self.redirect(self._bootstrap_url)
                raise tornado.web.Finish()
            return

        if not self.current_user:
            self.redirect(f'/login?{urlencode({"next": self.request.uri})}')
            raise tornado.web.Finish()

        username = self.current_user.decode('UTF-8')
        user = get_local_auth_user(self._db_path, username)
        if user is None or user['is_disabled'] or not user['is_admin']:
            raise tornado.web.HTTPError(403)

        self._current_username = username

    def _render_page(self, error_message=''):
        rows = []
        for user in list_local_auth_users(self._db_path):
            username_html = html.escape(user['username'])
            role = 'Admin' if user['is_admin'] else 'User'
            disabled = 'Yes' if user['is_disabled'] else 'No'
            delete_button = f"""
                <form action="{self._base_url}/delete" method="post" style="display:inline;">
                    <input type="hidden" name="username" value="{username_html}">
                    <button type="submit" class="btn btn-sm btn-outline-danger">Delete</button>
                </form>
            """
            rows.append(f"""
                <tr>
                    <td>{username_html}</td>
                    <td>{role}</td>
                    <td>{disabled}</td>
                    <td>{html.escape(user['last_login_at'] or 'Never')}</td>
                    <td>{delete_button}</td>
                </tr>
            """)

        error_html = ''
        if error_message:
            error_html = f"""<div class="alert alert-danger border-0 shadow-sm">{html.escape(error_message)}</div>"""

        page = f"""<!doctype html>
<html lang="en">
<head>
    <script src="https://cdn.jsdelivr.net/npm/jquery@3.6.1/dist/jquery.min.js"></script>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.1/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.1/dist/js/bootstrap.bundle.min.js"></script>
    <style>
        :root {{
            --page-bg: #eef2f6;
            --panel-bg: #ffffff;
            --panel-border: #d8e0e8;
            --text-main: #1f2937;
            --text-muted: #64748b;
            --accent: #184e77;
            --accent-strong: #123b5d;
        }}

        body {{
            margin: 0;
            min-height: 100vh;
            background:
                radial-gradient(circle at top right, rgba(24, 78, 119, 0.08), transparent 32%),
                linear-gradient(180deg, #f8fafc 0%, var(--page-bg) 100%);
            color: var(--text-main);
        }}

        .admin-shell {{
            padding: 28px;
        }}

        .admin-header {{
            display: flex;
            justify-content: space-between;
            align-items: end;
            gap: 20px;
            margin-bottom: 24px;
        }}

        .admin-kicker {{
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.14em;
            font-weight: 700;
            color: var(--accent);
            margin-bottom: 10px;
        }}

        .admin-header h1 {{
            margin: 0 0 8px 0;
            font-size: 2rem;
        }}

        .admin-header p {{
            margin: 0;
            color: var(--text-muted);
        }}

        .admin-actions {{
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
        }}

        .admin-card {{
            background: var(--panel-bg);
            border: 1px solid var(--panel-border);
            border-radius: 16px;
            box-shadow: 0 18px 40px rgba(15, 23, 42, 0.06);
        }}

        .admin-grid {{
            display: grid;
            grid-template-columns: 380px 1fr;
            gap: 22px;
            align-items: start;
        }}

        .admin-card .card-header {{
            background: transparent;
            border-bottom: 1px solid var(--panel-border);
            padding: 18px 22px 14px 22px;
            font-weight: 700;
        }}

        .admin-card .card-body {{
            padding: 22px;
        }}

        .section-note {{
            color: var(--text-muted);
            margin-top: -4px;
            margin-bottom: 18px;
        }}

        .form-label {{
            font-size: 0.88rem;
            font-weight: 600;
            color: #475569;
        }}

        .form-control {{
            border-radius: 10px;
            border-color: #ccd6df;
            min-height: 44px;
        }}

        .form-control:focus {{
            border-color: #7aa5c7;
            box-shadow: 0 0 0 0.2rem rgba(24, 78, 119, 0.12);
        }}

        .btn-primary {{
            background: linear-gradient(180deg, var(--accent) 0%, var(--accent-strong) 100%);
            border: 0;
        }}

        .table {{
            margin-bottom: 0;
        }}

        .table thead th {{
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #66758a;
            border-bottom-width: 1px;
        }}

        .table tbody td {{
            vertical-align: middle;
            padding-top: 14px;
            padding-bottom: 14px;
        }}

        .badge-role {{
            display: inline-block;
            min-width: 72px;
            padding: 7px 10px;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 700;
            text-align: center;
        }}

        .badge-admin {{
            background: #dceefb;
            color: #104a73;
        }}

        .badge-user {{
            background: #ebeff3;
            color: #556273;
        }}

        .badge-disabled {{
            background: #fff3e9;
            color: #9a4d00;
        }}

        .badge-active {{
            background: #e7f6ed;
            color: #1d6b3a;
        }}

        @media (max-width: 980px) {{
            .admin-shell {{
                padding: 18px;
            }}

            .admin-grid {{
                grid-template-columns: 1fr;
            }}

            .admin-header {{
                flex-direction: column;
                align-items: start;
            }}
        }}
    </style>
</head>
<body>
    <div class="admin-shell">
        <div class="admin-header">
            <div>
                <div class="admin-kicker">Administration</div>
                <h1>Local Access Management</h1>
                <p>Signed in as <strong>{html.escape(self._current_username)}</strong>. Create or remove local application users from this console.</p>
            </div>
            <div class="admin-actions">
                <a href="/" class="btn btn-outline-secondary">Back to App</a>
                <a href="/logout" class="btn btn-outline-secondary">Logout</a>
            </div>
        </div>
        {error_html}
        <div class="admin-grid">
            <div class="admin-card card">
                <div class="card-header">Create User</div>
                <div class="card-body">
                    <div class="section-note">Add a new local account. Administrators can access this management console.</div>
                    <form action="{self._base_url}/create" method="post">
                        <div class="mb-3">
                            <label class="form-label">Username</label>
                            <input name="username" class="form-control" placeholder="Enter username" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Temporary Password</label>
                            <input name="password" class="form-control" placeholder="Enter password" type="password" required>
                        </div>
                        <div class="form-check mb-4">
                            <input class="form-check-input" type="checkbox" value="1" id="is_admin" name="is_admin">
                            <label class="form-check-label" for="is_admin">Grant administrator access</label>
                        </div>
                        <button type="submit" class="btn btn-primary w-100">Create User</button>
                    </form>
                </div>
            </div>
            <div class="admin-card card">
                <div class="card-header">Existing Users</div>
                <div class="card-body">
                    <div class="section-note">Delete and recreate a user if credentials or role assignments need to change.</div>
                    <div class="table-responsive">
                        <table class="table align-middle">
                            <thead>
                                <tr>
                                    <th>User Name</th>
                                    <th>Role</th>
                                    <th>Status</th>
                                    <th>Last Login</th>
                                    <th>Action</th>
                                </tr>
                            </thead>
                            <tbody>
                                {''.join(rows).replace('<td>Admin</td>', '<td><span class="badge-role badge-admin">Admin</span></td>').replace('<td>User</td>', '<td><span class="badge-role badge-user">User</span></td>').replace('<td>Yes</td>', '<td><span class="badge-role badge-disabled">Disabled</span></td>').replace('<td>No</td>', '<td><span class="badge-role badge-active">Active</span></td>')}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>"""
        self.write(page)

    def _render_bootstrap_page(self, error_message=''):
        error_html = ''
        if error_message:
            error_html = f"""<div class="alert alert-danger border-0 shadow-sm">{html.escape(error_message)}</div>"""

        page = f"""<!doctype html>
<html lang="en">
<head>
    <script src="https://cdn.jsdelivr.net/npm/jquery@3.6.1/dist/jquery.min.js"></script>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.1/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.1/dist/js/bootstrap.bundle.min.js"></script>
    <style>
        :root {{
            --page-bg: #eef2f6;
            --panel-bg: #ffffff;
            --panel-border: #d8e0e8;
            --text-main: #1f2937;
            --text-muted: #64748b;
            --accent: #184e77;
            --accent-strong: #123b5d;
        }}

        body {{
            margin: 0;
            min-height: 100vh;
            background:
                radial-gradient(circle at top right, rgba(24, 78, 119, 0.08), transparent 30%),
                linear-gradient(180deg, #f8fafc 0%, var(--page-bg) 100%);
            color: var(--text-main);
        }}

        .bootstrap-shell {{
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 24px;
        }}

        .bootstrap-panel {{
            width: 100%;
            max-width: 980px;
            display: grid;
            grid-template-columns: 1.05fr 0.95fr;
            background: var(--panel-bg);
            border: 1px solid var(--panel-border);
            border-radius: 18px;
            overflow: hidden;
            box-shadow: 0 24px 60px rgba(15, 23, 42, 0.09);
        }}

        .bootstrap-brand {{
            padding: 42px;
            background:
                radial-gradient(circle at top right, rgba(24, 78, 119, 0.18), transparent 36%),
                linear-gradient(180deg, #fbfdff 0%, #edf3f8 100%);
            border-right: 1px solid var(--panel-border);
        }}

        .bootstrap-kicker {{
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.16em;
            font-weight: 700;
            color: var(--accent);
            margin-bottom: 16px;
        }}

        .bootstrap-brand h1 {{
            margin: 0 0 14px 0;
            font-size: 2.1rem;
            line-height: 1.1;
        }}

        .bootstrap-brand p {{
            color: var(--text-muted);
            line-height: 1.65;
            margin: 0 0 18px 0;
        }}

        .bootstrap-card-note {{
            padding: 16px 18px;
            background: rgba(255, 255, 255, 0.72);
            border: 1px solid var(--panel-border);
            border-radius: 12px;
            color: #405166;
        }}

        .bootstrap-form {{
            padding: 42px;
            display: flex;
            align-items: center;
        }}

        .bootstrap-form-card {{
            width: 100%;
            max-width: 360px;
            margin: 0 auto;
        }}

        .bootstrap-form-card h2 {{
            margin: 0 0 8px 0;
            font-size: 1.5rem;
        }}

        .bootstrap-form-card p {{
            margin: 0 0 22px 0;
            color: var(--text-muted);
        }}

        .form-label {{
            font-size: 0.88rem;
            font-weight: 600;
            color: #475569;
        }}

        .form-control {{
            border-radius: 10px;
            border-color: #ccd6df;
            min-height: 44px;
        }}

        .form-control:focus {{
            border-color: #7aa5c7;
            box-shadow: 0 0 0 0.2rem rgba(24, 78, 119, 0.12);
        }}

        .btn-primary {{
            background: linear-gradient(180deg, var(--accent) 0%, var(--accent-strong) 100%);
            border: 0;
            min-height: 46px;
        }}

        @media (max-width: 920px) {{
            .bootstrap-panel {{
                grid-template-columns: 1fr;
            }}

            .bootstrap-brand {{
                border-right: 0;
                border-bottom: 1px solid var(--panel-border);
                padding: 32px 28px;
            }}

            .bootstrap-form {{
                padding: 32px 28px;
            }}
        }}
    </style>
</head>
<body>
    <div class="bootstrap-shell">
        <div class="bootstrap-panel">
            <section class="bootstrap-brand">
                <div class="bootstrap-kicker">Initial Setup</div>
                <h1>Configure Local Access Management</h1>
                <p>No local authentication users exist for this application yet. Create the first administrator account to enable ongoing user management and secure sign-in.</p>
                <div class="bootstrap-card-note">
                    The first account created here is granted administrator access automatically and will be able to create or remove additional users.
                </div>
            </section>
            <section class="bootstrap-form">
                <div class="bootstrap-form-card">
                    <h2>Create first administrator</h2>
                    <p>Choose the credentials for the initial administrator account.</p>
                    {error_html}
                    <form action="{self._bootstrap_url}" method="post">
                        <div class="mb-3">
                            <label class="form-label">Administrator Username</label>
                            <input name="username" class="form-control" placeholder="Enter username" required autofocus>
                        </div>
                        <div class="mb-4">
                            <label class="form-label">Password</label>
                            <input name="password" class="form-control" placeholder="Enter password" type="password" required>
                        </div>
                        <button type="submit" class="btn btn-primary w-100">Create Administrator</button>
                    </form>
                </div>
            </section>
        </div>
    </div>
</body>
</html>"""
        self.write(page)


# --------------------------------------------------
#    Handlers
# --------------------------------------------------
class LocalAuthAdminPageHandler(_LocalAuthAdminBaseHandler):
    async def get(self):
        self._render_page(self.get_argument('error', ''))


class LocalAuthAdminBootstrapHandler(_LocalAuthAdminBaseHandler):
    async def get(self):
        if get_local_auth_user_count(self._db_path) != 0:
            self.redirect(self._base_url)
            return
        self._render_bootstrap_page(self.get_argument('error', ''))

    async def post(self):
        if get_local_auth_user_count(self._db_path) != 0:
            self.redirect(self._base_url)
            return

        username = self.get_argument('username', '').strip()
        password = self.get_argument('password', '')
        try:
            create_local_auth_user(self._db_path, username, password, is_admin=True)
        except Exception as e:
            self.redirect(f'{self._bootstrap_url}?{urlencode({"error": str(e)})}')
            return

        self.set_secure_cookie(self.settings['cookiename_user_auth_username'], username.encode('UTF-8'))
        self.set_secure_cookie(self.settings['cookiename_user_auth_method'], 'LocalAuth')
        self.redirect(self._base_url)


class LocalAuthAdminCreateHandler(_LocalAuthAdminBaseHandler):
    async def post(self):
        username = self.get_argument('username', '').strip()
        password = self.get_argument('password', '')
        is_admin = self.get_argument('is_admin', '') == '1'

        try:
            create_local_auth_user(self._db_path, username, password, is_admin=is_admin)
        except Exception as e:
            self.redirect(f'{self._base_url}?{urlencode({"error": str(e)})}')
            return

        self.redirect(self._base_url)


class LocalAuthAdminDeleteHandler(_LocalAuthAdminBaseHandler):
    async def post(self):
        username = self.get_argument('username', '').strip()
        if username == self._current_username:
            self.redirect(f'{self._base_url}?{urlencode({"error": "You cannot delete the currently signed-in admin user."})}')
            return

        try:
            delete_local_auth_user(self._db_path, username)
        except Exception as e:
            self.redirect(f'{self._base_url}?{urlencode({"error": str(e)})}')
            return

        self.redirect(self._base_url)


# --------------------------------------------------
#    Plugin
# --------------------------------------------------
class pluginLocalAuthAdmin:
    requires_cookie_secret = True

    def __init__(self, db_path, base_url='/admin/users'):
        self._db_path = db_path
        self._base_url = base_url.rstrip('/')

    def register(self, kwargs):
        kwargs.setdefault('route_handlers', [])
        kwargs['local_auth_bootstrap_url'] = self._base_url + '/bootstrap'
        kwargs['route_handlers'].extend([
            (self._base_url, LocalAuthAdminPageHandler, {'db_path': self._db_path, 'base_url': self._base_url}),
            (self._base_url + '/bootstrap', LocalAuthAdminBootstrapHandler, {'db_path': self._db_path, 'base_url': self._base_url}),
            (self._base_url + '/create', LocalAuthAdminCreateHandler, {'db_path': self._db_path, 'base_url': self._base_url}),
            (self._base_url + '/delete', LocalAuthAdminDeleteHandler, {'db_path': self._db_path, 'base_url': self._base_url}),
        ])
