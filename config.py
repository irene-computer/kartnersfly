import os
from dotenv import load_dotenv
import secrets

load_dotenv()

class Config:
    # ===== SECRETS =====
    SECRET_KEY = os.getenv('SECRET_KEY', secrets.token_hex(32))
    
    # ===== MODE =====
    DEBUG = os.getenv('DEBUG', 'False') == 'True'
    
    # ===== ADMIN =====
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', '')
    
    # ===== DATABASE =====
    DATABASE = os.getenv('DATABASE', 'database.db')
    
    # ===== SESSION =====
    PERMANENT_SESSION_LIFETIME = int(os.getenv('PERMANENT_SESSION_LIFETIME', 86400))
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'True') == 'True'
    SESSION_COOKIE_HTTPONLY = os.getenv('SESSION_COOKIE_HTTPONLY', 'True') == 'True'
    SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
    
    # ===== EMAIL =====
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True') == 'True'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', '')
    
    # ===== UPLOADS =====
    UPLOAD_FOLDER = 'static/images'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}
    
    # ===== SECURITE CSRF =====
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.getenv('CSRF_SECRET_KEY', secrets.token_hex(32))
    
    # ===== CONTACT =====
    PHONE = os.getenv('PHONE', '+237 676 268 350')
    EMAIL = os.getenv('EMAIL', '')