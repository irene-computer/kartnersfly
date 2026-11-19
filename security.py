"""
Protections transverses de Kartners Travel Agency :

- limitation durable des tentatives (stockée en base, partagée entre workers,
  conservée après un redémarrage) ;
- double authentification admin (codes TOTP, compatibles Google Authenticator,
  Microsoft Authenticator, Authy…) ;
- anti-robots des formulaires publics (champ piège + délai minimum de saisie) ;
- sauvegardes automatiques de la base SQLite.
"""
import base64
import datetime
import glob
import hashlib
import hmac
import os
import secrets
import sqlite3
import struct
import threading
import time

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from config import Config
import models


# ---------------------------------------------------------------------------
# Limitation durable (anti force brute / anti spam)
# ---------------------------------------------------------------------------

def init_security_tables():
    conn = models.get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS rate_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bucket TEXT NOT NULL,
            created_at REAL NOT NULL
        )
    ''')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_rate_bucket ON rate_events (bucket, created_at)')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS security_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event TEXT NOT NULL,
            ip TEXT,
            detail TEXT,
            created_at TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


def _bucket(kind, key):
    # On ne stocke pas l'IP en clair : empreinte salée par la clé secrète.
    digest = hmac.new(Config.SECRET_KEY.encode(), str(key).encode(), hashlib.sha256).hexdigest()[:32]
    return f"{kind}:{digest}"


def count_events(kind, key, window_seconds):
    conn = models.get_db()
    try:
        since = time.time() - window_seconds
        return conn.execute('SELECT COUNT(*) FROM rate_events WHERE bucket = ? AND created_at > ?',
                            (_bucket(kind, key), since)).fetchone()[0]
    finally:
        conn.close()


def record_event(kind, key):
    conn = models.get_db()
    try:
        now = time.time()
        conn.execute('INSERT INTO rate_events (bucket, created_at) VALUES (?, ?)', (_bucket(kind, key), now))
        # Ménage : on ne garde que les dernières 24 h.
        conn.execute('DELETE FROM rate_events WHERE created_at < ?', (now - 86400,))
        conn.commit()
    finally:
        conn.close()


def clear_events(kind, key):
    conn = models.get_db()
    try:
        conn.execute('DELETE FROM rate_events WHERE bucket = ?', (_bucket(kind, key),))
        conn.commit()
    finally:
        conn.close()


def over_limit(kind, key, limit, window_seconds):
    return count_events(kind, key, window_seconds) >= limit


def log_security_event(event, ip=None, detail=''):
    try:
        conn = models.get_db()
        conn.execute('INSERT INTO security_log (event, ip, detail, created_at) VALUES (?, ?, ?, ?)',
                     (event, ip, (detail or '')[:300], datetime.datetime.now().isoformat(timespec='seconds')))
        conn.execute("DELETE FROM security_log WHERE created_at < ?",
                     ((datetime.datetime.now() - datetime.timedelta(days=90)).isoformat(),))
        conn.commit()
        conn.close()
    except sqlite3.Error:
        pass
    print(f"[SECURITE] {event} ip={ip} {detail}")


def recent_security_events(limit=50):
    conn = models.get_db()
    try:
        return conn.execute('SELECT * FROM security_log ORDER BY id DESC LIMIT ?', (limit,)).fetchall()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Double authentification (TOTP, RFC 6238)
# ---------------------------------------------------------------------------

def _totp_at(secret_b32, counter):
    key = base64.b32decode(secret_b32.upper().replace(' ', '') + '=' * (-len(secret_b32.replace(' ', '')) % 8))
    digest = hmac.new(key, struct.pack('>Q', counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code = (struct.unpack('>I', digest[offset:offset + 4])[0] & 0x7FFFFFFF) % 1_000_000
    return f"{code:06d}"


def verify_totp(secret_b32, code, window=1):
    """Accepte le code courant et celui de ±30 s (décalage d'horloge du téléphone)."""
    code = (code or '').replace(' ', '')
    if not secret_b32 or len(code) != 6 or not code.isdigit():
        return False
    counter = int(time.time()) // 30
    try:
        return any(hmac.compare_digest(_totp_at(secret_b32, counter + d), code) for d in range(-window, window + 1))
    except (ValueError, base64.binascii.Error):
        return False


def new_totp_secret():
    return base64.b32encode(secrets.token_bytes(20)).decode().rstrip('=')


def totp_uri(secret_b32, account='admin'):
    from urllib.parse import quote
    return f"otpauth://totp/Kartners:{quote(account)}?secret={secret_b32}&issuer=Kartners%20Travel%20Agency"


# ---------------------------------------------------------------------------
# Anti-robots des formulaires publics
# ---------------------------------------------------------------------------

FORM_MIN_SECONDS = 3          # un humain met plus de 3 s à remplir un formulaire
FORM_MAX_AGE = 2 * 86400      # jeton valable 48 h


def _serializer():
    return URLSafeTimedSerializer(Config.SECRET_KEY, salt='kta-form')


def issue_form_token():
    return _serializer().dumps({'t': time.time()})


def check_form(data):
    """
    Retourne (ok, raison). `ok=False, raison='bot'` : rejet silencieux
    (on répond "succès" au robot sans rien enregistrer).
    """
    if (data.get('website') or '').strip():
        return False, 'bot'
    token = data.get('form_token') or ''
    try:
        payload = _serializer().loads(token, max_age=FORM_MAX_AGE)
    except SignatureExpired:
        return False, 'expired'
    except BadSignature:
        return False, 'invalid'
    if time.time() - float(payload.get('t', 0)) < FORM_MIN_SECONDS:
        return False, 'bot'
    return True, ''


# ---------------------------------------------------------------------------
# Sauvegardes automatiques de la base
# ---------------------------------------------------------------------------

BACKUP_KEEP = 14


def backup_dir():
    return Config.BACKUP_DIR or os.path.join(os.path.dirname(os.path.abspath(models.DB_PATH)), 'backups')


def make_backup(tag=None):
    """Copie cohérente de la base (API de sauvegarde SQLite), même pendant l'utilisation."""
    folder = backup_dir()
    os.makedirs(folder, exist_ok=True)
    name = f"database-{tag or datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.db"
    target = os.path.join(folder, name)
    src = sqlite3.connect(models.DB_PATH)
    dst = sqlite3.connect(target)
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()
    os.chmod(target, 0o600)
    for old in sorted(glob.glob(os.path.join(folder, 'database-*.db')))[:-BACKUP_KEEP]:
        try:
            os.remove(old)
        except OSError:
            pass
    return target


def list_backups():
    folder = backup_dir()
    files = sorted(glob.glob(os.path.join(folder, 'database-*.db')), reverse=True)
    return [{'name': os.path.basename(f), 'size': os.path.getsize(f),
             'date': datetime.datetime.fromtimestamp(os.path.getmtime(f))} for f in files]


def _daily_backup_loop():
    while True:
        try:
            today = datetime.date.today().strftime('%Y%m%d')
            if not glob.glob(os.path.join(backup_dir(), f'database-{today}*.db')):
                path = make_backup(f"{today}-auto")
                print(f"[SAUVEGARDE] {path}")
        except Exception as e:  # ne doit jamais arrêter le site
            print(f"[SAUVEGARDE] échec : {e}")
        time.sleep(3600)


_backup_started = False


def start_backup_thread():
    global _backup_started
    if _backup_started or not Config.AUTO_BACKUP:
        return
    _backup_started = True
    threading.Thread(target=_daily_backup_loop, daemon=True, name='kta-backup').start()
