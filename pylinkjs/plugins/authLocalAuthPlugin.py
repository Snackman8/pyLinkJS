# --------------------------------------------------
#    Imports
# --------------------------------------------------
import base64
import hashlib
import hmac
import os
import sqlite3
from datetime import datetime, timezone
from pylinkjs.PyLinkJS import LoginHandler, LogoutHandler


# --------------------------------------------------
#    Constants
# --------------------------------------------------
SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1
SCRYPT_DKLEN = 32


# --------------------------------------------------
#    Functions
# --------------------------------------------------
def _utcnow_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _get_db_conn(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _hash_password(password, salt=None):
    if salt is None:
        salt = os.urandom(16)
    password_hash = hashlib.scrypt(password.encode('UTF-8'),
                                   salt=salt,
                                   n=SCRYPT_N,
                                   r=SCRYPT_R,
                                   p=SCRYPT_P,
                                   dklen=SCRYPT_DKLEN)
    return 'scrypt$%d$%d$%d$%s$%s' % (
        SCRYPT_N,
        SCRYPT_R,
        SCRYPT_P,
        base64.b64encode(salt).decode('ASCII'),
        base64.b64encode(password_hash).decode('ASCII'))


def _verify_password(password, encoded_hash):
    try:
        algorithm, n, r, p, salt_b64, hash_b64 = encoded_hash.split('$', 5)
        if algorithm != 'scrypt':
            return False
        salt = base64.b64decode(salt_b64.encode('ASCII'))
        expected_hash = base64.b64decode(hash_b64.encode('ASCII'))
        candidate_hash = hashlib.scrypt(password.encode('UTF-8'),
                                        salt=salt,
                                        n=int(n),
                                        r=int(r),
                                        p=int(p),
                                        dklen=len(expected_hash))
        return hmac.compare_digest(candidate_hash, expected_hash)
    except Exception:
        return False


def init_local_auth_db(db_path):
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    with _get_db_conn(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                is_admin INTEGER NOT NULL DEFAULT 0,
                is_disabled INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                last_login_at TEXT
            )
        """)
        conn.commit()


def create_local_auth_user(db_path, username, password, is_admin=False):
    username = username.strip()
    if username == '':
        raise ValueError('username cannot be empty')
    if password == '':
        raise ValueError('password cannot be empty')

    init_local_auth_db(db_path)
    now = _utcnow_iso()
    with _get_db_conn(db_path) as conn:
        conn.execute("""
            INSERT INTO users (username, password_hash, is_admin, is_disabled, created_at, updated_at)
            VALUES (?, ?, ?, 0, ?, ?)
        """, (username, _hash_password(password), int(bool(is_admin)), now, now))
        conn.commit()


def set_local_auth_password(db_path, username, password):
    if password == '':
        raise ValueError('password cannot be empty')

    init_local_auth_db(db_path)
    now = _utcnow_iso()
    with _get_db_conn(db_path) as conn:
        cur = conn.execute("""
            UPDATE users
            SET password_hash = ?, updated_at = ?
            WHERE username = ?
        """, (_hash_password(password), now, username))
        conn.commit()
        if cur.rowcount == 0:
            raise ValueError(f'No local auth user found with username "{username}"')


def disable_local_auth_user(db_path, username, disabled=True):
    init_local_auth_db(db_path)
    now = _utcnow_iso()
    with _get_db_conn(db_path) as conn:
        cur = conn.execute("""
            UPDATE users
            SET is_disabled = ?, updated_at = ?
            WHERE username = ?
        """, (int(bool(disabled)), now, username))
        conn.commit()
        if cur.rowcount == 0:
            raise ValueError(f'No local auth user found with username "{username}"')


def delete_local_auth_user(db_path, username):
    init_local_auth_db(db_path)
    with _get_db_conn(db_path) as conn:
        cur = conn.execute("""
            DELETE FROM users
            WHERE username = ?
        """, (username,))
        conn.commit()
        if cur.rowcount == 0:
            raise ValueError(f'No local auth user found with username "{username}"')


def get_local_auth_user(db_path, username):
    init_local_auth_db(db_path)
    with _get_db_conn(db_path) as conn:
        row = conn.execute("""
            SELECT id, username, is_admin, is_disabled, created_at, updated_at, last_login_at
            FROM users
            WHERE username = ?
        """, (username,)).fetchone()
        if row is None:
            return None
        return dict(row)


def list_local_auth_users(db_path):
    init_local_auth_db(db_path)
    with _get_db_conn(db_path) as conn:
        rows = conn.execute("""
            SELECT id, username, is_admin, is_disabled, created_at, updated_at, last_login_at
            FROM users
            ORDER BY username ASC
        """).fetchall()
        return [dict(row) for row in rows]


def get_local_auth_user_count(db_path):
    init_local_auth_db(db_path)
    with _get_db_conn(db_path) as conn:
        row = conn.execute("SELECT COUNT(*) FROM users").fetchone()
        return 0 if row is None else int(row[0])


# --------------------------------------------------
#    Plugin
# --------------------------------------------------
class pluginLocalAuth:
    requires_cookie_secret = True

    def __init__(self, db_path, login_html_page=None, logout_post_action_url=None):
        if login_html_page is None:
            login_html_page = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'authLocalAuthPlugin_Login.html')

        self._kwargs = {
            'login_handler': LocalAuthLoginHandler,
            'logout_handler': LocalAuthLogoutHandler,
            'login_html_page': login_html_page,
            'local_auth_db_path': db_path, }

        init_local_auth_db(db_path)

        if logout_post_action_url is not None:
            self._kwargs['logout_post_action_url'] = logout_post_action_url

    def register(self, kwargs):
        kwargs.update(self._kwargs)


# --------------------------------------------------
#    LoginHandler
# --------------------------------------------------
class LocalAuthLoginHandler(LoginHandler):
    def _render_login(self, error_message=''):
        filename = self.application.settings['login_html_page']
        with open(filename, 'r') as f:
            s = f.read()
        s = s.replace('{next_url}', self.get_argument('next', '/'))
        s = s.replace('{error_message}', error_message)
        self.write(s)

    async def get(self):
        db_path = self.settings['local_auth_db_path']
        bootstrap_url = self.settings.get('local_auth_bootstrap_url')
        if bootstrap_url and get_local_auth_user_count(db_path) == 0:
            self.redirect(bootstrap_url)
            return
        self._render_login()

    async def post(self):
        username = self.request.arguments['username'][0].decode('UTF-8').strip()
        password = self.request.arguments['password'][0].decode('UTF-8')
        db_path = self.settings['local_auth_db_path']
        bootstrap_url = self.settings.get('local_auth_bootstrap_url')

        if bootstrap_url and get_local_auth_user_count(db_path) == 0:
            self.redirect(bootstrap_url)
            return

        if username == '' or password == '':
            self._render_login('Login Failed!')
            return

        with _get_db_conn(db_path) as conn:
            row = conn.execute("""
                SELECT username, password_hash, is_disabled
                FROM users
                WHERE username = ?
            """, (username,)).fetchone()

            if row is None or row['is_disabled'] or not _verify_password(password, row['password_hash']):
                self._render_login('Login Failed!')
                return

            conn.execute("""
                UPDATE users
                SET last_login_at = ?, updated_at = ?
                WHERE username = ?
            """, (_utcnow_iso(), _utcnow_iso(), username))
            conn.commit()

        cookies = {
            self.settings['cookiename_user_auth_username']: username.encode('UTF-8'),
            self.settings['cookiename_user_auth_method']: 'LocalAuth'}
        self.post_handler(cookies)


# --------------------------------------------------
#    LogoutHandler
# --------------------------------------------------
class LocalAuthLogoutHandler(LogoutHandler):
    async def get(self):
        cookie_list = [self.settings['cookiename_user_auth_username'],
                       self.settings['cookiename_user_auth_method']]
        self.get_handler(cookie_list)
