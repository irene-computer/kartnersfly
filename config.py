import os
from dotenv import load_dotenv
import secrets

load_dotenv()


def _env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in ('1', 'true', 'yes', 'on')


def _persistent_secret(path):
    """
    Clé secrète stable : sans elle, chaque worker gunicorn générait sa propre
    clé et les sessions admin étaient perdues au hasard. Si SECRET_KEY n'est
    pas défini, la clé est créée une fois puis conservée à côté de la base.
    """
    try:
        if os.path.exists(path):
            with open(path) as f:
                key = f.read().strip()
                if key:
                    return key
        key = secrets.token_hex(32)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w') as f:
            f.write(key)
        return key
    except FileExistsError:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        return secrets.token_hex(32)


class Config:
    DEBUG = _env_bool('DEBUG')

    # ===== ADMIN =====
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', '').strip()
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', '').strip()
    # Optionnel : empreinte du mot de passe (générée par `python manage_security.py hash`)
    # à la place du mot de passe en clair.
    ADMIN_PASSWORD_HASH = os.getenv('ADMIN_PASSWORD_HASH', '').strip()
    # Double authentification : secret TOTP (généré par `python manage_security.py totp`).
    ADMIN_TOTP_SECRET = os.getenv('ADMIN_TOTP_SECRET', '').strip().replace(' ', '')

    # ===== DATABASE (chemin absolu + création du dossier) =====
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATABASE = os.getenv('DATABASE', os.path.join(BASE_DIR, 'database.db'))

    db_dir = os.path.dirname(DATABASE)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    # ===== SECRETS =====
    SECRET_KEY = os.getenv('SECRET_KEY') or _persistent_secret(os.path.join(db_dir or BASE_DIR, '.secret_key'))

    # ===== SESSION =====
    PERMANENT_SESSION_LIFETIME = int(os.getenv('PERMANENT_SESSION_LIFETIME', 86400))
    # Cookie "Secure" (HTTPS uniquement) : activé par défaut sur Fly.io, désactivé
    # en local pour que la connexion admin fonctionne sur http://localhost.
    SESSION_COOKIE_SECURE = _env_bool('SESSION_COOKIE_SECURE', default=bool(os.getenv('FLY_APP_NAME')))
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')

    # ===== EMAIL =====
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = _env_bool('MAIL_USE_TLS', True)
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', '')

    # ===== ALERTES À L'AGENCE (nouvelle réservation, message, candidature) =====
    NOTIFY_EMAIL = os.getenv('NOTIFY_EMAIL', '').strip() or os.getenv('EMAIL', 'kta2k23@gmail.com')
    CALLMEBOT_PHONE = os.getenv('CALLMEBOT_PHONE', '').strip()      # ex. 237676268350
    CALLMEBOT_APIKEY = os.getenv('CALLMEBOT_APIKEY', '').strip()

    # ===== UPLOADS =====
    # Dossier persistant pour les images envoyées depuis l'admin (ex. /data/uploads
    # sur le volume Fly.io). Vide = images stockées dans static/images.
    UPLOAD_ROOT = os.getenv('UPLOAD_ROOT', '').strip()
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    # ===== SAUVEGARDES =====
    # Une copie de la base par jour, 14 conservées (dossier backups/ à côté de la base).
    AUTO_BACKUP = _env_bool('AUTO_BACKUP', True)
    BACKUP_DIR = os.getenv('BACKUP_DIR', '').strip()

    # ===== CONTACT =====
    PHONE = os.getenv('PHONE', '+237 676 268 350')
    EMAIL = os.getenv('EMAIL', 'kta2k23@gmail.com')