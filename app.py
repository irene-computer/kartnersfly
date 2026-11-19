from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, Response, send_from_directory
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import Config
import security
from werkzeug.security import check_password_hash, generate_password_hash
from flask import g
from markupsafe import Markup
from models import get_db, init_db
import datetime
import os
import smtplib
import ssl
from email.message import EmailMessage
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
import json
import uuid
import re
import csv
from io import StringIO
import secrets
from functools import wraps
import traceback
import hmac
import shutil
import threading
import time
from urllib.parse import urlparse

from models import (
    add_scholarship,
    get_all_scholarships,
    get_pending_scholarships_count,
    update_scholarship_status,
    delete_scholarship,
    get_scholarship_by_id,
    get_all_user_emails,
    get_all_newsletter_emails,
    add_scholarship_opportunity,
    get_all_scholarship_opportunities,
    delete_scholarship_opportunity,
    get_scholarship_opportunity_by_id,
    update_scholarship_opportunity,
    add_destination,
    get_all_destinations,
    get_destination_by_id,
    update_destination,
    delete_destination,
    get_all_services,
    add_service,
    update_service,
    update_service_image,
    delete_service,
    get_service_by_id,
    get_services_count,
    add_booking,
    get_all_bookings,
    update_booking_status,
    delete_booking,
    get_pending_bookings_count,
    subscribe_newsletter,
    get_newsletter_count,
    get_all_newsletter_emails,
    get_unread_messages_count,
    get_all_messages,
    add_message,
    mark_message_as_read,
    delete_message,
    get_destinations_count,
    get_scholarships_ending_soon,
    migrate_image_paths,
)

app = Flask(__name__)
app.config.from_object(Config)

if not Config.ADMIN_USERNAME or not Config.ADMIN_PASSWORD:
    print("[ATTENTION] ADMIN_USERNAME / ADMIN_PASSWORD non définis : la connexion admin est désactivée.")

# Derrière le proxy de Fly.io : vraie IP du visiteur (limitation de débit) et HTTPS.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(hours=8)
app.config['TEMPLATES_AUTO_RELOAD'] = Config.DEBUG

if Config.DEBUG:
    CORS(app)
else:
    CORS(app, resources={r"/api/*": {"origins": [
        "https://www.kartnersagency.com", "https://kartnersagency.com", "https://kartnersfly.fly.dev"]}})

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],
    storage_uri=os.getenv('RATELIMIT_STORAGE_URI', 'memory://')
)

def sanitize_input(data):
    if isinstance(data, dict):
        return {k: sanitize_input(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_input(item) for item in data]
    elif isinstance(data, str):
        # Jinja échappe déjà le HTML à l'affichage : on garde les apostrophes
        # (indispensables en français) et on retire seulement les balises et
        # les caractères de contrôle.
        data = re.sub(r'<[^>]*>', '', data)
        data = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', data)
        return data.strip()
    return data

EMAIL_RE = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


def is_valid_email(value):
    return bool(value) and len(value) <= 254 and bool(EMAIL_RE.match(value))


def get_json_payload():
    """Retourne le corps JSON (ou le formulaire) sous forme de dict, jamais None."""
    data = request.get_json(silent=True)
    if data is None:
        data = request.form.to_dict() if request.form else {}
    if not isinstance(data, dict):
        data = {}
    return sanitize_input(data)


def api_error(message, status=400):
    return jsonify({'success': False, 'message': message}), status

def guard_public_form(kind, data, per_hour, success_message):
    """
    Contrôles anti-robots et anti-spam communs aux formulaires publics.
    Retourne une réponse à renvoyer immédiatement, ou None si tout va bien.
    """
    ip = request.remote_addr or 'inconnue'
    ok, reason = security.check_form(data)
    if not ok and reason == 'bot':
        security.log_security_event('robot bloqué', ip, kind)
        # On répond "succès" pour ne pas aider le robot à s'adapter.
        return jsonify({'success': True, 'message': success_message})
    if not ok:
        return api_error("La page a expiré. Rechargez-la puis renvoyez le formulaire.", 400)
    if security.over_limit(f'form-{kind}', ip, per_hour, 3600):
        security.log_security_event('envois bloqués', ip, kind)
        return api_error("Vous avez envoyé beaucoup de demandes. Réessayez dans une heure ou appelez-nous.", 429)
    security.record_event(f'form-{kind}', ip)
    return None


# Routes d'administration qui modifient des données via un simple lien (GET).
ADMIN_GET_ACTIONS = ('/delete/', '/confirm/', '/read/', '/admin/fix-images', '/admin/test-email')


def _same_origin():
    """Vérifie que la requête vient bien du site (protection CSRF)."""
    source = request.headers.get('Origin') or request.headers.get('Referer')
    if not source:
        return False
    return urlparse(source).netloc == request.host


@app.before_request
def before_request_security():
    g.csp_nonce = secrets.token_urlsafe(16)
    if request.content_length and request.content_length > Config.MAX_CONTENT_LENGTH:
        return jsonify({'error': 'Fichier trop volumineux'}), 413

    if request.method in ['POST', 'PUT', 'PATCH']:
        ctype = request.content_type or ''
        allowed = ('multipart/form-data', 'application/x-www-form-urlencoded', 'application/json')
        if ctype and not any(a in ctype for a in allowed):
            return jsonify({'error': 'Unsupported Media Type'}), 415

    # Protection CSRF de l'administration : toute action qui modifie des
    # données doit provenir d'une page du site lui-même.
    path = request.path
    is_admin_area = path.startswith('/admin') or path.startswith('/api/scholarship/')
    if is_admin_area and session.get('admin_logged_in'):
        changes_data = request.method in ('POST', 'PUT', 'PATCH', 'DELETE') or any(a in path for a in ADMIN_GET_ACTIONS)
        if changes_data and not _same_origin():
            flash("Action refusée : la requête ne provient pas du site.", 'danger')
            return redirect(url_for('admin_dashboard'))


@app.after_request
def security_headers(response):
    response.headers.setdefault('X-Content-Type-Options', 'nosniff')
    response.headers.setdefault('X-Frame-Options', 'SAMEORIGIN')
    response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
    response.headers.setdefault('Permissions-Policy', 'camera=(), microphone=(), geolocation=()')
    response.headers.setdefault('Cross-Origin-Opener-Policy', 'same-origin')
    if request.is_secure:
        # HSTS : le navigateur n'utilisera plus jamais http:// pour ce site (1 an).
        response.headers.setdefault('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')
    if response.mimetype == 'text/html':
        response.headers['Content-Security-Policy'] = _content_security_policy()
    if request.path.startswith('/admin'):
        response.headers['Cache-Control'] = 'no-store'
    return response


def _content_security_policy():
    """
    Liste blanche des sources autorisées. Sur le site public, seuls les scripts
    du site et les blocs portant le "nonce" de la page s'exécutent : un script
    injecté par un attaquant est bloqué par le navigateur. L'admin (ancien
    code avec attributs onclick) garde les scripts en ligne, mais rien d'autre.
    """
    nonce = getattr(g, 'csp_nonce', '')
    common = [
        "default-src 'self'",
        "base-uri 'self'",
        "object-src 'none'",
        "frame-ancestors 'self'",
        "form-action 'self'",
        "img-src 'self' data: https:",
        "font-src 'self' data: https://fonts.gstatic.com https://cdnjs.cloudflare.com",
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com https://cdn.jsdelivr.net",
        "connect-src 'self'",
        "frame-src https://www.google.com https://maps.google.com",
        "manifest-src 'self'",
        "worker-src 'self'",
    ]
    if request.path.startswith('/admin'):
        common.append("script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com")
    else:
        common.append(f"script-src 'self' 'nonce-{nonce}'")
    if request.is_secure:
        common.append('upgrade-insecure-requests')
    return '; '.join(common)


def _credentials_fingerprint():
    raw = f"{Config.ADMIN_USERNAME}|{Config.ADMIN_PASSWORD}|{Config.ADMIN_PASSWORD_HASH}|{Config.ADMIN_TOTP_SECRET}"
    return hmac.new(Config.SECRET_KEY.encode(), raw.encode(), 'sha256').hexdigest()[:24]


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login', next=request.path))
        if session.get('admin_fp') != _credentials_fingerprint():
            # Mot de passe ou 2FA changés depuis la connexion : session révoquée.
            session.clear()
            flash('Session expirée, reconnectez-vous.', 'info')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return wrapper

UPLOAD_FOLDER = os.path.join(app.static_folder, 'images')
# SVG exclu : un SVG peut contenir du JavaScript exécuté sur le domaine du site.
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
UPLOAD_SUBFOLDERS = ['flags', 'destinations', 'services', 'scholarships']


def setup_persistent_uploads():
    """
    Sur Fly.io, le disque du conteneur est effacé à chaque déploiement : les
    images envoyées depuis l'admin disparaissaient. Si UPLOAD_ROOT est défini
    (ex. /data/uploads, sur le volume persistant), chaque dossier
    static/images/<sous-dossier> devient un lien vers ce volume. Les images
    livrées avec le code y sont recopiées si elles n'y sont pas encore.
    """
    root = Config.UPLOAD_ROOT
    for sub in UPLOAD_SUBFOLDERS:
        local = os.path.join(UPLOAD_FOLDER, sub)
        try:
            if not root:
                os.makedirs(local, exist_ok=True)
                continue
            target = os.path.join(root, sub)
            os.makedirs(target, exist_ok=True)
            if os.path.islink(local):
                continue
            if os.path.isdir(local):
                for name in os.listdir(local):
                    src, dst = os.path.join(local, name), os.path.join(target, name)
                    if os.path.isfile(src) and not os.path.exists(dst):
                        shutil.copy2(src, dst)
                os.rename(local, f"{local}.bundled-{os.getpid()}")
            os.symlink(target, local)
            print(f"[OK] Uploads '{sub}' stockés sur {target}")
        except FileExistsError:
            pass  # un autre worker gunicorn a déjà créé le lien
        except OSError as e:
            print(f"[ATTENTION] Stockage persistant indisponible pour '{sub}' : {e}")
            os.makedirs(local, exist_ok=True)


setup_persistent_uploads()


def allowed_file(filename):
    return bool(filename) and '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_image(file, subfolder='scholarships'):
    if not file or not allowed_file(file.filename):
        return None
    filename = secure_filename(file.filename)
    unique_name = f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}_{filename}"
    folder = os.path.join(UPLOAD_FOLDER, subfolder)
    os.makedirs(folder, exist_ok=True)
    file.save(os.path.join(folder, unique_name))
    return f"images/{subfolder}/{unique_name}"


def remove_uploaded_image(rel_path):
    """Supprime une image envoyée (jamais les images par défaut ni les URL externes)."""
    if not rel_path or rel_path.startswith(('http://', 'https://')):
        return
    if os.path.basename(rel_path).startswith('default.'):
        return
    full = os.path.realpath(os.path.join(app.static_folder, rel_path))
    if not full.startswith(os.path.realpath(UPLOAD_FOLDER)):
        return
    try:
        if os.path.isfile(full):
            os.remove(full)
    except OSError:
        pass

init_db()
security.init_security_tables()
security.start_backup_thread()

# Codes pays ISO pour afficher un drapeau quand l'image locale manque.
COUNTRY_CODES = {
    'france': 'fr', 'emirats arabes unis': 'ae', 'émirats arabes unis': 'ae', 'eau': 'ae',
    'maroc': 'ma', 'maldives': 'mv', 'italie': 'it', 'japon': 'jp', 'etats-unis': 'us',
    'états-unis': 'us', 'usa': 'us', 'royaume-uni': 'gb', 'canada': 'ca', 'suisse': 'ch',
    'turquie': 'tr', 'grece': 'gr', 'grèce': 'gr', 'senegal': 'sn', 'sénégal': 'sn',
    'egypte': 'eg', 'égypte': 'eg', 'indonesie': 'id', 'indonésie': 'id', 'australie': 'au',
    'belgique': 'be', 'allemagne': 'de', 'espagne': 'es', 'pays-bas': 'nl', 'chine': 'cn',
    "cote d'ivoire": 'ci', "côte d'ivoire": 'ci', 'gabon': 'ga', 'afrique du sud': 'za',
    'cameroun': 'cm', 'nigeria': 'ng', 'ghana': 'gh', 'portugal': 'pt', 'russie': 'ru',
    'inde': 'in', 'thailande': 'th', 'thaïlande': 'th', 'bresil': 'br', 'brésil': 'br',
    'tunisie': 'tn', 'algerie': 'dz', 'algérie': 'dz', 'kenya': 'ke', 'rwanda': 'rw',
    'qatar': 'qa', 'arabie saoudite': 'sa', 'irlande': 'ie', 'autriche': 'at', 'pologne': 'pl',
}

# Code aéroport affiché sur les cartes (départ : Douala, DLA).
CITY_AIRPORTS = {
    'paris': 'CDG', 'dubai': 'DXB', 'dubaï': 'DXB', 'marrakech': 'RAK', 'maldives': 'MLE',
    'rome': 'FCO', 'tokyo': 'HND', 'new york': 'JFK', 'londres': 'LHR', 'montreal': 'YUL',
    'montréal': 'YUL', 'zurich': 'ZRH', 'istanbul': 'IST', 'athenes': 'ATH', 'athènes': 'ATH',
    'dakar': 'DSS', 'le caire': 'CAI', 'bali': 'DPS', 'sydney': 'SYD', 'bruxelles': 'BRU',
    'berlin': 'BER', 'madrid': 'MAD', 'abidjan': 'ABJ', 'libreville': 'LBV', 'casablanca': 'CMN',
    'toronto': 'YYZ', 'genève': 'GVA', 'geneve': 'GVA', 'lisbonne': 'LIS', 'johannesburg': 'JNB',
    'nairobi': 'NBO', 'lagos': 'LOS', 'accra': 'ACC', 'doha': 'DOH', 'pékin': 'PEK', 'pekin': 'PEK',
}


@app.template_filter('img')
def img_filter(path):
    """URL d'une image stockée en base, ou '' si le fichier n'existe pas."""
    if not path:
        return ''
    path = str(path).strip()
    if path.startswith(('http://', 'https://')):
        return path
    if path.startswith('/static/'):
        path = path[len('/static/'):]
    if not path.startswith('images/'):
        path = 'images/' + path
    full = os.path.join(app.static_folder, path)
    if not os.path.isfile(full) or os.path.getsize(full) < 200:
        return ''  # absent, ou image "par défaut" de 1 pixel
    return url_for('static', filename=path)


@app.template_filter('flag')
def flag_filter(path, country=''):
    """Drapeau : image locale si elle existe, sinon drapeau flagcdn d'après le pays."""
    url = img_filter(path)
    if url:
        return url
    code = COUNTRY_CODES.get((country or '').strip().lower())
    return f"https://flagcdn.com/w80/{code}.png" if code else ''


@app.template_filter('airport')
def airport_filter(name):
    key = (name or '').strip().lower()
    if key in CITY_AIRPORTS:
        return CITY_AIRPORTS[key]
    letters = re.sub(r'[^A-Za-z]', '', name or '')
    return (letters[:3] or '---').upper()


@app.template_filter('money')
def money_filter(value):
    try:
        return f"{float(value):,.0f}".replace(',', '\u202f')
    except (TypeError, ValueError):
        return '—'


@app.template_filter('date_fr')
def date_fr_filter(value):
    mois = ['janv.', 'févr.', 'mars', 'avr.', 'mai', 'juin', 'juil.', 'août', 'sept.', 'oct.', 'nov.', 'déc.']
    try:
        d = datetime.date.fromisoformat(str(value)[:10])
        return f"{d.day} {mois[d.month - 1]} {d.year}"
    except (TypeError, ValueError):
        return value or ''


def _honeypot():
    # Champ invisible pour les humains : un robot qui le remplit est ignoré.
    return Markup('<div class="hp" aria-hidden="true"><label>Ne pas remplir '
                  '<input type="text" name="website" tabindex="-1" autocomplete="off"></label></div>')


@app.context_processor
def utility_processor():
    def now():
        return datetime.datetime.now()
    scholarships_pending = 0
    if request.path.startswith('/admin'):
        try:
            scholarships_pending = get_pending_scholarships_count()
        except Exception:
            scholarships_pending = 0
    return dict(now=now, scholarships_pending=scholarships_pending,
                csp_nonce=getattr(g, 'csp_nonce', ''), form_token=security.issue_form_token,
                m_honeypot=_honeypot,
                contact_phone=Config.PHONE, contact_email=Config.EMAIL,
                whatsapp_number=re.sub(r'\D', '', Config.PHONE))

# ============================================================
# FONCTIONS EMAIL CORRIGÉES AVEC LOGS DÉTAILLÉS
# ============================================================

def send_confirmation_email(to_email, booking_data):
    """
    Envoie un email de confirmation de réservation.
    Retourne True si l'envoi a réussi, False sinon.
    """
    try:
        smtp_server = Config.MAIL_SERVER
        smtp_port = Config.MAIL_PORT
        sender_email = Config.MAIL_USERNAME
        sender_password = Config.MAIL_PASSWORD

        if not sender_email or not sender_password:
            print("[ERREUR] Email non configuré : MAIL_USERNAME ou MAIL_PASSWORD manquants.")
            return False

        msg = EmailMessage()
        msg['Subject'] = f"Confirmation de réservation - KTA-{booking_data['id']}"
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Reply-To'] = sender_email

        text_content = f"""
KARTNERS TRAVEL AGENCY - CONFIRMATION DE RÉSERVATION

Bonjour {booking_data['fullname']},

Votre réservation est confirmée.

Destination: {booking_data['destination_name']}
Date de départ: {booking_data['departure_date']}
Voyageurs: {booking_data['travelers']}

Kartners Travel Agency
Tel: {Config.PHONE}
Email: {Config.EMAIL}

Pour plus d'informations, visitez notre site : https://www.kartnersagency.com
        """
        msg.set_content(text_content)

        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls(context=context)
            server.login(sender_email, sender_password)
            server.send_message(msg)

        print(f"[SUCCES] Email de confirmation envoyé à {to_email}")
        return True

    except smtplib.SMTPAuthenticationError as e:
        print(f"[ERREUR AUTH] Échec d'authentification SMTP : {e}")
        print("  -> Vérifiez votre mot de passe d'application Gmail ou les identifiants.")
        return False
    except smtplib.SMTPException as e:
        print(f"[ERREUR SMTP] Problème d'envoi : {e}")
        return False
    except Exception as e:
        print(f"[ERREUR] Envoi email : {str(e)}")
        traceback.print_exc()
        return False

def send_bulk_email(recipients, subject, html_content, text_content=None):
    """
    Envoie un email en masse (newsletter).
    Retourne (success_count, fail_count).
    """
    if not recipients:
        return 0, 0
    try:
        smtp_server = Config.MAIL_SERVER
        smtp_port = Config.MAIL_PORT
        sender_email = Config.MAIL_USERNAME
        sender_password = Config.MAIL_PASSWORD

        if not sender_email or not sender_password:
            print("[ERREUR] Email non configuré pour l'envoi groupé.")
            return 0, len(recipients)

        if text_content is None:
            text_content = re.sub(r'<[^>]+>', '', html_content)

        context = ssl.create_default_context()
        success_count, fail_count = 0, 0

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls(context=context)
            server.login(sender_email, sender_password)
            for recipient in recipients:
                try:
                    msg = EmailMessage()
                    msg['Subject'] = subject
                    msg['From'] = sender_email
                    msg['To'] = recipient
                    msg['Reply-To'] = sender_email
                    msg.set_content(text_content)
                    msg.add_alternative(html_content, subtype='html')
                    server.send_message(msg)
                    success_count += 1
                    print(f"[SUCCES] Email envoyé à {recipient}")
                except Exception as e:
                    fail_count += 1
                    print(f"[ERREUR] Envoi à {recipient}: {str(e)}")
        print(f"[BILAN] {success_count} envoyés, {fail_count} échecs.")
        return success_count, fail_count
    except Exception as e:
        print(f"[ERREUR] Envoi de masse: {str(e)}")
        traceback.print_exc()
        return 0, len(recipients)

def send_scholarship_notification(recipients, scholarship_data):
    subject = f"Nouvelle opportunité de bourse - Kartners Travel Agency"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Nouvelle opportunité de bourse</title>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .header {{ background: linear-gradient(135deg, #8B5CF6, #3B82F6); color: white; padding: 30px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 24px; }}
            .header p {{ margin: 10px 0 0; opacity: 0.9; }}
            .content {{ padding: 30px; }}
            .info-block {{ background: #f8f9fa; border-radius: 8px; padding: 20px; margin-bottom: 20px; }}
            .info-block h3 {{ margin: 0 0 15px; color: #6B3FA0; }}
            .btn {{ display: inline-block; padding: 12px 30px; background: linear-gradient(135deg, #8B5CF6, #3B82F6); color: white; text-decoration: none; border-radius: 50px; font-weight: 600; }}
            .footer {{ background: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #6c757d; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>KARTNERS TRAVEL AGENCY</h1>
                <p>Voyagez, comme vous l'imaginez</p>
            </div>
            <div class="content">
                <h2>Nouvelle opportunité de bourse d'études</h2>
                <p>Bonjour,</p>
                <p>Nous avons le plaisir de vous informer qu'une nouvelle opportunité de bourse est disponible.</p>

                <div class="info-block">
                    <h3>Détails de l'opportunité</h3>
                    <p><strong>Pays :</strong> {scholarship_data.get('country', 'À déterminer')}</p>
                    <p><strong>Niveau d'étude :</strong> {scholarship_data.get('study_level', 'À déterminer')}</p>
                    <p><strong>Domaine :</strong> {scholarship_data.get('field_of_study', 'À déterminer')}</p>
                    <p><strong>Date limite :</strong> {scholarship_data.get('deadline', 'Consultez notre site')}</p>
                </div>

                <p style="text-align: center; margin: 30px 0;">
                    <a href="https://www.kartnersagency.com/bourse-etudes" class="btn">En savoir plus</a>
                </p>
                <p style="text-align: center; margin-top: 20px;">
                    <a href="https://www.kartnersagency.com">Visitez notre site</a>
                </p>
            </div>
            <div class="footer">
                <p>&copy; 2026 Kartners Travel Agency</p>
                <p>Tel: {Config.PHONE} | Email: {Config.EMAIL}</p>
                <p><a href="https://www.kartnersagency.com">www.kartnersagency.com</a></p>
            </div>
        </div>
    </body>
    </html>
    """

    text_content = f"""
KARTNERS TRAVEL AGENCY - NOUVELLE OPPORTUNITÉ DE BOURSE

Bonjour,

Une nouvelle opportunité de bourse est disponible.

Détails:
- Pays: {scholarship_data.get('country', 'À déterminer')}
- Niveau: {scholarship_data.get('study_level', 'À déterminer')}
- Domaine: {scholarship_data.get('field_of_study', 'À déterminer')}

Pour en savoir plus: https://www.kartnersagency.com/bourse-etudes

Visitez notre site : https://www.kartnersagency.com
    """

    return send_bulk_email(recipients, subject, html_content, text_content)

# ============================================================
# ROUTES CLIENT
# ============================================================

@app.route('/')
def home():
    conn = get_db()
    destinations_list = conn.execute('SELECT * FROM destinations ORDER BY price LIMIT 6').fetchall()
    services_list = conn.execute('SELECT * FROM services ORDER BY id LIMIT 6').fetchall()
    destinations_total = conn.execute('SELECT COUNT(*) FROM destinations').fetchone()[0]
    conn.close()
    opportunities = [o for o in get_all_scholarship_opportunities()
                     if not o['end_date'] or o['end_date'] >= datetime.date.today().isoformat()]
    return render_template('index.html', destinations=destinations_list, services=services_list,
                           destinations_total=destinations_total, opportunities=opportunities[:3])

@app.route('/destinations')
def destinations():
    conn = get_db()
    destinations_list = conn.execute('SELECT * FROM destinations ORDER BY name').fetchall()
    conn.close()
    return render_template('destinations.html', destinations=destinations_list,
                           query=request.args.get('q', '').strip(),
                           selected_id=request.args.get('reserver', type=int))

@app.route('/services')
def services_page():
    conn = get_db()
    services_list = conn.execute('SELECT * FROM services ORDER BY id').fetchall()
    conn.close()
    return render_template('services.html', services=services_list)

@app.route('/about')
def about():
    conn = get_db()
    services_list = conn.execute('SELECT * FROM services ORDER BY id').fetchall()
    conn.close()
    return render_template('about.html', services=services_list)

@app.route('/contact')
def contact():
    return render_template('contact.html', selected_service=request.args.get('service', ''))

@app.route('/mentions-legales')
def mentions_legales():
    return render_template('legal/mentions.html')

@app.route('/cgv')
def cgv():
    return render_template('legal/cgv.html')

@app.route('/politique-confidentialite')
def confidentialite():
    return render_template('legal/confidentialite.html')

# ----- PWA : le manifeste et le service worker doivent être servis à la racine -----
@app.route('/manifest.json')
def manifest():
    return send_from_directory(app.root_path, 'manifest.json', mimetype='application/manifest+json')

@app.route('/sw.js')
def service_worker():
    response = send_from_directory(app.static_folder, 'sw.js', mimetype='application/javascript')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['Service-Worker-Allowed'] = '/'
    return response

@app.route('/robots.txt')
def robots():
    return Response("User-agent: *\nDisallow: /admin\n", mimetype='text/plain')

@app.errorhandler(404)
def page_not_found(e):
    if request.path.startswith('/api/'):
        return api_error('Ressource introuvable', 404)
    return render_template('404.html'), 404

@app.errorhandler(429)
def too_many_requests(e):
    return api_error('Trop de tentatives. Patientez une minute puis réessayez.', 429)

@app.errorhandler(500)
def server_error(e):
    if request.path.startswith('/api/'):
        return api_error('Erreur interne. Réessayez dans un instant.', 500)
    return render_template('404.html', server_error=True), 500

# ============================================================
# API CLIENT
# ============================================================

@app.route('/api/contact', methods=['POST'])
@limiter.limit("5 per minute")
def api_contact():
    data = get_json_payload()
    blocked = guard_public_form('contact', data, 10, 'Merci ! Notre équipe vous répond sous 24 h.')
    if blocked:
        return blocked
    name, email, message = data.get('name', ''), data.get('email', ''), data.get('message', '')
    if not name or not email or not message:
        return api_error('Merci de renseigner votre nom, votre email et votre message.')
    if not is_valid_email(email):
        return api_error('Adresse email invalide.')
    if len(message) > 2000 or len(name) > 120:
        return api_error('Message trop long (2000 caractères maximum).')
    try:
        add_message(name, email, data.get('phone', '')[:40], data.get('service', '')[:60], message)
    except Exception:
        traceback.print_exc()
        return api_error("Votre message n'a pas pu être enregistré. Réessayez ou appelez-nous.", 500)
    return jsonify({'success': True, 'message': 'Merci ! Notre équipe vous répond sous 24 h.'})

@app.route('/api/scholarship', methods=['POST'])
@limiter.limit("10 per minute")
def api_scholarship():
    data = get_json_payload()
    blocked = guard_public_form('bourse', data, 10, 'Candidature reçue ! Un conseiller vous recontacte sous 24 h.')
    if blocked:
        return blocked
    labels = {'full_name': 'nom complet', 'email': 'email', 'country': 'pays souhaité',
              'study_level': "niveau d'études", 'field_of_study': "domaine d'études"}
    for field, label in labels.items():
        if not data.get(field):
            return api_error(f'Le champ « {label} » est obligatoire.')
    if not is_valid_email(data['email']):
        return api_error('Adresse email invalide.')
    try:
        scholarship_id = add_scholarship(
            full_name=data['full_name'][:120],
            email=data['email'],
            phone=data.get('phone', '')[:40],
            country=data['country'][:80],
            study_level=data['study_level'][:80],
            field_of_study=data['field_of_study'][:80],
            message=data.get('message', '')[:2000]
        )
    except Exception:
        traceback.print_exc()
        scholarship_id = None
    if not scholarship_id:
        return api_error("Votre candidature n'a pas pu être enregistrée. Réessayez.", 500)
    return jsonify({'success': True, 'message': 'Candidature reçue ! Un conseiller vous recontacte sous 24 h.'})

@app.route('/api/booking', methods=['POST'])
@limiter.limit("5 per minute")
def api_booking():
    data = get_json_payload()
    blocked = guard_public_form('reservation', data, 10, 'Demande envoyée. Un conseiller vous contacte sous 24 h pour confirmer.')
    if blocked:
        return blocked
    labels = {'fullname': 'nom complet', 'email': 'email', 'phone': 'téléphone', 'departure_date': 'date de départ'}
    for field, label in labels.items():
        if not data.get(field):
            return api_error(f'Le champ « {label} » est obligatoire.')
    if not is_valid_email(data['email']):
        return api_error('Adresse email invalide.')

    try:
        departure = datetime.date.fromisoformat(str(data['departure_date'])[:10])
    except ValueError:
        return api_error('Date de départ invalide.')
    if departure < datetime.date.today():
        return api_error('La date de départ doit être aujourd\'hui ou plus tard.')

    try:
        travelers = int(data.get('travelers') or 1)
    except (TypeError, ValueError):
        travelers = 0
    if not 1 <= travelers <= 50:
        return api_error('Le nombre de voyageurs doit être compris entre 1 et 50.')

    try:
        destination_id = int(data['destination_id']) if data.get('destination_id') else None
    except (TypeError, ValueError):
        destination_id = None

    conn = get_db()
    try:
        destination_name = data.get('destination_name', '')
        if destination_id:
            dest = conn.execute('SELECT name FROM destinations WHERE id = ?', (destination_id,)).fetchone()
            if dest:
                destination_name = dest['name']
            else:
                destination_id = None
        cursor = conn.execute('''
            INSERT INTO bookings (
                destination_id, destination_name, fullname, email, phone,
                departure_date, travelers, message, created_at, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'en attente')
        ''', (
            destination_id, destination_name[:120], data['fullname'][:120], data['email'],
            data['phone'][:40], departure.isoformat(), travelers, data.get('message', '')[:2000],
            datetime.datetime.now().isoformat()
        ))
        conn.commit()
        last_id = cursor.lastrowid
    except Exception:
        traceback.print_exc()
        return api_error("La réservation n'a pas pu être enregistrée. Réessayez.", 500)
    finally:
        conn.close()

    return jsonify({'success': True, 'id': last_id,
                    'message': f'Demande KTA-{last_id} envoyée. Un conseiller vous contacte sous 24 h pour confirmer.'})

@app.route('/api/newsletter', methods=['POST'])
@limiter.limit("10 per minute")
def api_newsletter():
    data = get_json_payload()
    blocked = guard_public_form('newsletter', data, 5, 'Inscription confirmée. À bientôt dans votre boîte mail !')
    if blocked:
        return blocked
    email = (data.get('email') or '').lower()
    if not is_valid_email(email):
        return api_error('Adresse email invalide.')
    try:
        conn = get_db()
        conn.execute('INSERT OR IGNORE INTO newsletter (email, created_at) VALUES (?, ?)',
                     (email, datetime.datetime.now().isoformat()))
        conn.commit()
        conn.close()
    except Exception:
        traceback.print_exc()
        return api_error("Inscription impossible pour le moment. Réessayez plus tard.", 500)
    return jsonify({'success': True, 'message': 'Inscription confirmée. À bientôt dans votre boîte mail !'})

# ============================================================
# ADMIN
# ============================================================

def _safe_next(target):
    if target and target.startswith('/admin') and not target.startswith('//'):
        return target
    return url_for('admin_dashboard')

LOGIN_MAX_PER_IP = 5          # échecs autorisés par adresse IP…
LOGIN_IP_WINDOW = 15 * 60     # …sur 15 minutes
LOGIN_MAX_GLOBAL = 30         # échecs tous visiteurs confondus…
LOGIN_GLOBAL_WINDOW = 60 * 60 # …sur 1 heure (attaque distribuée)


def _password_ok(password):
    if Config.ADMIN_PASSWORD_HASH:
        try:
            return check_password_hash(Config.ADMIN_PASSWORD_HASH, password)
        except ValueError:
            return False
    return hmac.compare_digest(password.encode(), Config.ADMIN_PASSWORD.encode())


@app.route('/admin/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute", methods=['POST'])
def admin_login():
    if session.get('admin_logged_in') and session.get('admin_fp') == _credentials_fingerprint():
        return redirect(url_for('admin_dashboard'))
    needs_totp = bool(Config.ADMIN_TOTP_SECRET)
    if request.method == 'GET':
        return render_template('admin/login.html', needs_totp=needs_totp)

    ip = request.remote_addr or 'inconnue'
    if not Config.ADMIN_USERNAME or not (Config.ADMIN_PASSWORD or Config.ADMIN_PASSWORD_HASH):
        error = "Connexion désactivée : définissez ADMIN_USERNAME et ADMIN_PASSWORD sur le serveur."
        return render_template('admin/login.html', error=error, needs_totp=needs_totp), 503

    if (security.over_limit('login-ip', ip, LOGIN_MAX_PER_IP, LOGIN_IP_WINDOW)
            or security.over_limit('login-all', 'all', LOGIN_MAX_GLOBAL, LOGIN_GLOBAL_WINDOW)):
        security.log_security_event('connexion bloquée', ip, 'trop de tentatives')
        error = "Trop de tentatives échouées. Réessayez dans 15 minutes."
        return render_template('admin/login.html', error=error, needs_totp=needs_totp), 429

    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    code = request.form.get('totp', '').strip()

    valid = hmac.compare_digest(username.encode(), Config.ADMIN_USERNAME.encode())
    valid = _password_ok(password) and valid
    if valid and needs_totp:
        valid = security.verify_totp(Config.ADMIN_TOTP_SECRET, code)

    if not valid:
        security.record_event('login-ip', ip)
        security.record_event('login-all', 'all')
        security.log_security_event('échec de connexion admin', ip, f"identifiant saisi : {username[:40]}")
        time.sleep(0.5)  # ralentit les essais automatisés
        error = 'Identifiants ou code de vérification incorrects' if needs_totp else 'Identifiants incorrects'
        return render_template('admin/login.html', error=error, needs_totp=needs_totp), 401

    security.clear_events('login-ip', ip)
    security.log_security_event('connexion admin réussie', ip)
    session.clear()
    session['admin_logged_in'] = True
    session['admin_username'] = username
    session['admin_fp'] = _credentials_fingerprint()
    session.permanent = True
    flash('Connexion réussie', 'success')
    return redirect(_safe_next(request.args.get('next')))

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    flash('Déconnexion réussie', 'info')
    return redirect(url_for('admin_login'))

@app.route('/admin')
def admin_root():
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    conn = get_db()
    messages_non_lus = conn.execute("SELECT COUNT(*) FROM messages WHERE status = 'non lu'").fetchone()[0]
    messages_total = conn.execute('SELECT COUNT(*) FROM messages').fetchone()[0]
    bookings_en_attente = conn.execute("SELECT COUNT(*) FROM bookings WHERE status = 'en attente'").fetchone()[0]
    bookings_total = conn.execute('SELECT COUNT(*) FROM bookings').fetchone()[0]
    destinations_count = conn.execute('SELECT COUNT(*) FROM destinations').fetchone()[0]
    services_count = conn.execute('SELECT COUNT(*) FROM services').fetchone()[0]
    newsletter_count = conn.execute('SELECT COUNT(*) FROM newsletter').fetchone()[0]
    scholarships_pending = get_pending_scholarships_count()
    scholarships_total = conn.execute('SELECT COUNT(*) FROM scholarships').fetchone()[0]
    derniers_messages = conn.execute('SELECT * FROM messages ORDER BY created_at DESC LIMIT 5').fetchall()
    derniers_scholarships = conn.execute('SELECT * FROM scholarships ORDER BY created_at DESC LIMIT 5').fetchall()
    conn.close()
    return render_template('admin/dashboard.html',
                           messages_non_lus=messages_non_lus,
                           messages_total=messages_total,
                           bookings_en_attente=bookings_en_attente,
                           bookings_total=bookings_total,
                           destinations_count=destinations_count,
                           services_count=services_count,
                           newsletter_count=newsletter_count,
                           scholarships_pending=scholarships_pending,
                           scholarships_total=scholarships_total,
                           derniers_messages=derniers_messages,
                           derniers_scholarships=derniers_scholarships)

@app.route('/admin/messages')
@login_required
def admin_messages():
    conn = get_db()
    messages = conn.execute('SELECT * FROM messages ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('admin/messages.html', messages=messages)

@app.route('/admin/message/read/<int:id>')
@login_required
def admin_message_read(id):
    conn = get_db()
    conn.execute("UPDATE messages SET status = 'lu' WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash('Message marqué comme lu', 'success')
    return redirect(url_for('admin_messages'))

@app.route('/admin/message/delete/<int:id>')
@login_required
def admin_message_delete(id):
    conn = get_db()
    conn.execute('DELETE FROM messages WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Message supprimé', 'success')
    return redirect(url_for('admin_messages'))

# ========== DESTINATIONS ==========
@app.route('/admin/destinations')
@login_required
def admin_destinations():
    conn = get_db()
    destinations_list = conn.execute('SELECT * FROM destinations ORDER BY name').fetchall()
    conn.close()
    return render_template('admin/destinations_admin.html', destinations=destinations_list)

@app.route('/admin/destination/add', methods=['POST'])
@login_required
def admin_destination_add():
    try:
        name = sanitize_input(request.form.get('name'))
        country = sanitize_input(request.form.get('country'))
        description = sanitize_input(request.form.get('description'))
        price = float(request.form.get('price'))
        continent = sanitize_input(request.form.get('continent', 'europe'))

        flag_file = request.files.get('flag_image')
        flag_path = save_uploaded_image(flag_file, 'flags') if flag_file else None
        if not flag_path:
            flag_path = 'images/flags/default.png'

        dest_file = request.files.get('destination_image')
        dest_path = save_uploaded_image(dest_file, 'destinations') if dest_file else None
        if not dest_path:
            dest_path = 'images/destinations/default.jpg'

        add_destination(name, country, flag_path, description, price, dest_path, continent)
        flash('Destination ajoutée avec succès', 'success')
        return redirect(url_for('admin_destinations'))
    except Exception as e:
        traceback.print_exc()
        flash(f'Erreur : {str(e)}', 'danger')
        return redirect(url_for('admin_destinations'))

@app.route('/admin/destination/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_destination_edit(id):
    destination = get_destination_by_id(id)
    if not destination:
        flash('Destination introuvable', 'danger')
        return redirect(url_for('admin_destinations'))
    if request.method == 'POST':
        conn = get_db()
        try:
            name = sanitize_input(request.form.get('name'))
            country = sanitize_input(request.form.get('country'))
            description = sanitize_input(request.form.get('description'))
            price = float(request.form.get('price'))
            continent = sanitize_input(request.form.get('continent', 'europe'))

            old = conn.execute('SELECT flag_image, image FROM destinations WHERE id = ?', (id,)).fetchone()
            flag_path = old['flag_image']
            dest_path = old['image']

            if request.form.get('remove_flag') == 'on':
                if flag_path and not flag_path.endswith('default.png'):
                    old_flag = os.path.join(UPLOAD_FOLDER, flag_path.replace('images/', ''))
                    if os.path.exists(old_flag):
                        try: os.remove(old_flag)
                        except: pass
                flag_path = 'images/flags/default.png'

            if request.form.get('remove_dest_image') == 'on':
                if dest_path and not dest_path.endswith('default.jpg'):
                    old_dest = os.path.join(UPLOAD_FOLDER, dest_path.replace('images/', ''))
                    if os.path.exists(old_dest):
                        try: os.remove(old_dest)
                        except: pass
                dest_path = 'images/destinations/default.jpg'

            flag_file = request.files.get('flag_image')
            if flag_file and allowed_file(flag_file.filename):
                if flag_path and not flag_path.endswith('default.png'):
                    old_flag = os.path.join(UPLOAD_FOLDER, flag_path.replace('images/', ''))
                    if os.path.exists(old_flag):
                        try: os.remove(old_flag)
                        except: pass
                flag_path = save_uploaded_image(flag_file, 'flags')

            dest_file = request.files.get('destination_image')
            if dest_file and allowed_file(dest_file.filename):
                if dest_path and not dest_path.endswith('default.jpg'):
                    old_dest = os.path.join(UPLOAD_FOLDER, dest_path.replace('images/', ''))
                    if os.path.exists(old_dest):
                        try: os.remove(old_dest)
                        except: pass
                dest_path = save_uploaded_image(dest_file, 'destinations')

            update_destination(id, name, country, flag_path, description, price, dest_path, continent)
            flash('Destination mise à jour avec succès', 'success')
            return redirect(url_for('admin_destinations'))
        except Exception as e:
            traceback.print_exc()
            flash(f'Erreur : {str(e)}', 'danger')
            return redirect(url_for('admin_destinations'))
        finally:
            conn.close()
    return render_template('admin/destination_edit.html', destination=destination)

@app.route('/admin/destination/delete/<int:id>')
@login_required
def admin_destination_delete(id):
    try:
        delete_destination(id)
        flash('Destination supprimée', 'success')
    except Exception as e:
        traceback.print_exc()
        flash(f'Erreur : {str(e)}', 'danger')
    return redirect(url_for('admin_destinations'))

# ========== SERVICES ==========
@app.route('/admin/services')
@login_required
def admin_services():
    conn = get_db()
    services_list = conn.execute('SELECT * FROM services ORDER BY name').fetchall()
    conn.close()
    return render_template('admin/services_admin.html', services=services_list)

@app.route('/admin/service/add', methods=['GET', 'POST'])
@login_required
def admin_service_add():
    if request.method == 'POST':
        try:
            name = sanitize_input(request.form.get('name'))
            description = sanitize_input(request.form.get('description'))
            icon = sanitize_input(request.form.get('icon'))
            features = sanitize_input(request.form.get('features', ''))
            image_file = request.files.get('image')
            image_path = save_uploaded_image(image_file, 'services') if image_file else 'images/services/default.jpg'
            add_service(name, description, icon, image_path, features)
            flash('Service ajouté avec succès', 'success')
            return redirect(url_for('admin_services'))
        except Exception as e:
            traceback.print_exc()
            flash(f'Erreur : {str(e)}', 'danger')
            return redirect(url_for('admin_service_add'))
    return render_template('admin/service_edit.html', service=None)

@app.route('/admin/service/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_service_edit(id):
    service = get_service_by_id(id)
    if not service:
        flash('Service non trouvé', 'danger')
        return redirect(url_for('admin_services'))
    if request.method == 'POST':
        try:
            name = sanitize_input(request.form.get('name'))
            description = sanitize_input(request.form.get('description'))
            icon = sanitize_input(request.form.get('icon'))
            features = sanitize_input(request.form.get('features', ''))
            remove_image = request.form.get('remove_image') == 'on'
            image_file = request.files.get('image')

            image_path = service['image']
            if remove_image:
                if image_path and not image_path.endswith('default.jpg'):
                    old = os.path.join(UPLOAD_FOLDER, image_path.replace('images/', ''))
                    if os.path.exists(old):
                        try: os.remove(old)
                        except: pass
                image_path = 'images/services/default.jpg'

            if image_file and allowed_file(image_file.filename):
                if image_path and not image_path.endswith('default.jpg') and not remove_image:
                    old = os.path.join(UPLOAD_FOLDER, image_path.replace('images/', ''))
                    if os.path.exists(old):
                        try: os.remove(old)
                        except: pass
                image_path = save_uploaded_image(image_file, 'services')

            update_service(id, name, description, icon, image_path, features)
            flash('Service mis à jour avec succès', 'success')
            return redirect(url_for('admin_services'))
        except Exception as e:
            traceback.print_exc()
            flash(f'Erreur : {str(e)}', 'danger')
    return render_template('admin/service_edit.html', service=service)

@app.route('/admin/service/delete/<int:id>')
@login_required
def admin_service_delete(id):
    try:
        service = get_service_by_id(id)
        if service and service['image'] and not service['image'].endswith('default.jpg'):
            old_path = os.path.join(UPLOAD_FOLDER, service['image'].replace('images/', ''))
            if os.path.exists(old_path):
                try: os.remove(old_path)
                except: pass
        delete_service(id)
        flash('Service supprimé avec succès', 'success')
    except Exception as e:
        traceback.print_exc()
        flash(f'Erreur : {str(e)}', 'danger')
    return redirect(url_for('admin_services'))

# ========== BOOKINGS ==========
@app.route('/admin/bookings')
@login_required
def admin_bookings():
    conn = get_db()
    bookings = conn.execute('''
        SELECT b.*, d.name as dest_name, d.country as dest_country, d.image as dest_image
        FROM bookings b
        LEFT JOIN destinations d ON b.destination_id = d.id
        ORDER BY b.created_at DESC
    ''').fetchall()
    total = len(bookings)
    pending = len([b for b in bookings if b['status'] == 'en attente'])
    confirmed = len([b for b in bookings if b['status'] == 'confirmee'])
    cancelled = len([b for b in bookings if b['status'] == 'annulee'])
    conn.close()
    return render_template('admin/bookings.html', bookings=bookings, total=total, pending=pending, confirmed=confirmed, cancelled=cancelled)

@app.route('/admin/booking/details/<int:id>')
@login_required
def admin_booking_details(id):
    conn = get_db()
    booking = conn.execute('''
        SELECT b.*, d.name as dest_name, d.country as dest_country, d.image as dest_image
        FROM bookings b
        LEFT JOIN destinations d ON b.destination_id = d.id
        WHERE b.id = ?
    ''', (id,)).fetchone()
    conn.close()
    if not booking:
        flash('Réservation non trouvée', 'danger')
        return redirect(url_for('admin_bookings'))
    return render_template('admin/booking_details.html', booking=booking)

@app.route('/admin/booking/confirm/<int:id>')
@login_required
def admin_booking_confirm(id):
    conn = get_db()
    booking = conn.execute('SELECT * FROM bookings WHERE id = ?', (id,)).fetchone()
    if booking:
        conn.execute("UPDATE bookings SET status = 'confirmee' WHERE id = ?", (id,))
        conn.commit()
        booking_data = {
            'id': booking['id'],
            'fullname': booking['fullname'],
            'destination_name': booking['destination_name'],
            'departure_date': booking['departure_date'],
            'travelers': booking['travelers']
        }
        email_sent = send_confirmation_email(booking['email'], booking_data)
        if email_sent:
            flash('Réservation confirmée et email envoyé au client', 'success')
        else:
            flash('Réservation confirmée mais email non envoyé (erreur technique) – consultez les logs.', 'warning')
    else:
        flash('Réservation non trouvée', 'danger')
    conn.close()
    return redirect(url_for('admin_bookings'))

@app.route('/admin/booking/update/<int:id>', methods=['POST'])
@login_required
def admin_booking_update(id):
    status = request.form.get('status')
    if status not in ('en attente', 'confirmee', 'annulee'):
        flash('Statut invalide', 'danger')
        return redirect(url_for('admin_bookings'))
    conn = get_db()
    conn.execute('UPDATE bookings SET status = ? WHERE id = ?', (status, id))
    conn.commit()
    conn.close()
    flash('Statut mis à jour', 'success')
    return redirect(url_for('admin_bookings'))

@app.route('/admin/booking/delete/<int:id>')
@login_required
def admin_booking_delete(id):
    try:
        delete_booking(id)
        flash('Réservation supprimée', 'success')
    except Exception as e:
        traceback.print_exc()
        flash(f'Erreur : {str(e)}', 'danger')
    return redirect(url_for('admin_bookings'))

@app.route('/admin/booking/export')
@login_required
def admin_booking_export():
    conn = get_db()
    bookings = conn.execute('''
        SELECT b.*, d.name as dest_name
        FROM bookings b
        LEFT JOIN destinations d ON b.destination_id = d.id
        ORDER BY b.created_at DESC
    ''').fetchall()
    conn.close()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Nom', 'Email', 'Téléphone', 'Destination', 'Date départ', 'Voyageurs', 'Statut', 'Date réservation'])
    def cell(value):
        value = '' if value is None else str(value)
        return "'" + value if value[:1] in ('=', '+', '-', '@') else value
    for b in bookings:
        writer.writerow([cell(v) for v in (
            b['id'], b['fullname'], b['email'], b['phone'],
            b['destination_name'] or b['dest_name'],
            b['departure_date'], b['travelers'],
            b['status'], b['created_at']
        )])
    response = Response('\ufeff' + output.getvalue(), mimetype='text/csv; charset=utf-8')
    response.headers['Content-Disposition'] = 'attachment; filename=reservations.csv'
    return response

# ========== NEWSLETTER ==========
@app.route('/admin/newsletter')
@login_required
def admin_newsletter():
    conn = get_db()
    subscribers = conn.execute('SELECT * FROM newsletter ORDER BY created_at DESC').fetchall()
    count = conn.execute('SELECT COUNT(*) FROM newsletter').fetchone()[0]
    conn.close()
    return render_template('admin/newsletter.html', subscribers=subscribers, count=count)

@app.route('/admin/newsletter/send', methods=['POST'])
@login_required
def admin_newsletter_send():
    try:
        subject = sanitize_input(request.form.get('subject'))
        content = request.form.get('content')
        if not subject or not content:
            flash('Veuillez remplir tous les champs', 'danger')
            return redirect(url_for('admin_newsletter'))
        recipients = get_all_newsletter_emails()
        if not recipients:
            flash('Aucun abonné à la newsletter', 'warning')
            return redirect(url_for('admin_newsletter'))

        # Construction du HTML avec le lien vers le site
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{subject}</title>
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #8B5CF6, #3B82F6); color: white; padding: 30px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 24px; }}
                .header p {{ margin: 10px 0 0; opacity: 0.9; }}
                .content {{ padding: 30px; }}
                .footer {{ background: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #6c757d; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>KARTNERS TRAVEL AGENCY</h1>
                    <p>Voyagez, comme vous l'imaginez</p>
                </div>
                <div class="content">
                    <p><a href="https://www.kartnersagency.com" style="display:inline-block; padding:10px 20px; background:#8B5CF6; color:white; text-decoration:none; border-radius:50px;">Visitez notre site</a></p>
                    {content}
                </div>
                <div class="footer">
                    <p>&copy; 2026 Kartners Travel Agency</p>
                    <p>Tel: {Config.PHONE} | Email: {Config.EMAIL}</p>
                    <p><a href="https://www.kartnersagency.com">www.kartnersagency.com</a></p>
                </div>
            </div>
        </body>
        </html>
        """

        text_content = re.sub(r'<[^>]+>', '', content)
        success, fail = send_bulk_email(recipients, subject, html_content, text_content)

        if success > 0:
            flash(f'Newsletter envoyée. {success} emails envoyés, {fail} échecs.', 'success')
        else:
            flash(f'Échec total de l\'envoi. {fail} échecs. Vérifiez les logs.', 'danger')

        return redirect(url_for('admin_newsletter'))
    except Exception as e:
        traceback.print_exc()
        flash(f'Erreur : {str(e)}', 'danger')
        return redirect(url_for('admin_newsletter'))

@app.route('/admin/newsletter/delete/<int:id>')
@login_required
def admin_newsletter_delete(id):
    try:
        conn = get_db()
        conn.execute('DELETE FROM newsletter WHERE id = ?', (id,))
        conn.commit()
        conn.close()
        flash('Abonné supprimé', 'success')
    except Exception as e:
        traceback.print_exc()
        flash(f'Erreur : {str(e)}', 'danger')
    return redirect(url_for('admin_newsletter'))

# ========== SCHOLARSHIPS (Demandes) ==========
@app.route('/admin/scholarships')
@login_required
def admin_scholarships():
    scholarships = get_all_scholarships()
    return render_template('admin/scholarships.html', scholarships=scholarships)

@app.route('/api/scholarship/<int:scholarship_id>')
@login_required
def api_get_scholarship(scholarship_id):
    try:
        scholarship = get_scholarship_by_id(scholarship_id)
        if scholarship:
            return jsonify(dict(scholarship))
        return jsonify({'error': 'Demande non trouvée'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/scholarship/update/<int:scholarship_id>', methods=['POST'])
@login_required
def api_update_scholarship(scholarship_id):
    try:
        data = request.get_json(silent=True) or {}
        status = data.get('status')
        if status not in ('en attente', 'en cours', 'acceptee', 'refusee'):
            return jsonify({'success': False, 'message': 'Statut requis'}), 400
        update_scholarship_status(scholarship_id, status)
        return jsonify({'success': True, 'message': 'Statut mis à jour'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/scholarship/delete/<int:scholarship_id>', methods=['POST'])
@login_required
def api_delete_scholarship(scholarship_id):
    try:
        delete_scholarship(scholarship_id)
        return jsonify({'success': True, 'message': 'Demande supprimée'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ========== ADMIN SCHOLARSHIP OPPORTUNITIES ==========
@app.route('/admin/scholarship_opportunities')
@login_required
def admin_scholarship_opportunities():
    opportunities = get_all_scholarship_opportunities()
    return render_template('admin/scholarship_opportunities.html', opportunities=opportunities)

@app.route('/admin/scholarship_opportunities/add', methods=['GET', 'POST'])
@login_required
def admin_scholarship_add():
    if request.method == 'POST':
        try:
            title = sanitize_input(request.form.get('title'))
            country = sanitize_input(request.form.get('country'))
            study_level = sanitize_input(request.form.get('study_level'))
            field_of_study = sanitize_input(request.form.get('field_of_study'))
            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date')
            description = sanitize_input(request.form.get('description'))
            benefits = sanitize_input(request.form.get('benefits'))
            requirements = sanitize_input(request.form.get('requirements'))

            flag_file = request.files.get('flag_image')
            image_file = request.files.get('image')

            flag_url = save_uploaded_image(flag_file, 'scholarships') if flag_file else None
            if not flag_url:
                flag_url = sanitize_input(request.form.get('flag_url', ''))

            image_url = save_uploaded_image(image_file, 'scholarships') if image_file else None
            if not image_url:
                image_url = sanitize_input(request.form.get('image_url', ''))

            add_scholarship_opportunity(
                title, country, study_level, field_of_study,
                start_date, end_date, flag_url, image_url,
                description, benefits, requirements
            )

            scholarship_data = {
                'country': country,
                'study_level': study_level,
                'field_of_study': field_of_study,
                'deadline': end_date or 'Consultez notre site'
            }
            # Seuls les abonnés à la newsletter ont accepté de recevoir ces emails.
            recipients = get_all_newsletter_emails()
            if recipients:
                threading.Thread(target=send_scholarship_notification,
                                 args=(recipients, scholarship_data), daemon=True).start()
                flash(f'Bourse ajoutée. Notification en cours d\'envoi à {len(recipients)} abonné(s).', 'success')
            else:
                flash('Bourse ajoutée avec succès !', 'success')
            return redirect(url_for('admin_scholarship_opportunities'))
        except Exception as e:
            traceback.print_exc()
            flash(f'Erreur : {str(e)}', 'danger')
            return redirect(url_for('admin_scholarship_add'))
    return render_template('admin/scholarship_add.html')

@app.route('/admin/scholarship_opportunities/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_scholarship_edit(id):
    opportunity = get_scholarship_opportunity_by_id(id)
    if not opportunity:
        flash('Bourse non trouvée', 'danger')
        return redirect(url_for('admin_scholarship_opportunities'))

    if request.method == 'POST':
        try:
            title = sanitize_input(request.form.get('title'))
            country = sanitize_input(request.form.get('country'))
            study_level = sanitize_input(request.form.get('study_level'))
            field_of_study = sanitize_input(request.form.get('field_of_study'))
            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date')
            description = sanitize_input(request.form.get('description'))
            benefits = sanitize_input(request.form.get('benefits'))
            requirements = sanitize_input(request.form.get('requirements'))

            flag_file = request.files.get('flag_image')
            image_file = request.files.get('image')
            flag_url = opportunity['flag_url']
            image_url = opportunity['image_url']

            if flag_file and allowed_file(flag_file.filename):
                if flag_url and not flag_url.startswith('http'):
                    old_flag = os.path.join(UPLOAD_FOLDER, flag_url.replace('images/', ''))
                    if os.path.exists(old_flag):
                        try: os.remove(old_flag)
                        except: pass
                flag_url = save_uploaded_image(flag_file, 'scholarships')
            else:
                new_flag_url = sanitize_input(request.form.get('flag_url', ''))
                if new_flag_url:
                    flag_url = new_flag_url

            if image_file and allowed_file(image_file.filename):
                if image_url and not image_url.startswith('http'):
                    old_img = os.path.join(UPLOAD_FOLDER, image_url.replace('images/', ''))
                    if os.path.exists(old_img):
                        try: os.remove(old_img)
                        except: pass
                image_url = save_uploaded_image(image_file, 'scholarships')
            else:
                new_image_url = sanitize_input(request.form.get('image_url', ''))
                if new_image_url:
                    image_url = new_image_url

            update_scholarship_opportunity(
                id, title, country, study_level, field_of_study,
                start_date, end_date, flag_url, image_url,
                description, benefits, requirements
            )
            flash('Bourse modifiée avec succès !', 'success')
            return redirect(url_for('admin_scholarship_opportunities'))
        except Exception as e:
            traceback.print_exc()
            flash(f'Erreur : {str(e)}', 'danger')
            return redirect(url_for('admin_scholarship_edit', id=id))

    return render_template('admin/scholarship_edit.html', opportunity=opportunity)

@app.route('/admin/scholarship_opportunities/delete/<int:id>', methods=['POST'])
@login_required
def admin_scholarship_opportunity_delete(id):
    try:
        opp = get_scholarship_opportunity_by_id(id)
        if opp:
            for field in ['flag_url', 'image_url']:
                val = opp[field]
                if val and not val.startswith('http') and not val.endswith(('default.png', 'default.jpg')):
                    path = os.path.join(UPLOAD_FOLDER, val.replace('images/', ''))
                    if os.path.exists(path):
                        try: os.remove(path)
                        except: pass
        delete_scholarship_opportunity(id)
        flash('Bourse supprimée avec succès.', 'success')
    except Exception as e:
        traceback.print_exc()
        flash(f'Erreur : {str(e)}', 'danger')
    return redirect(url_for('admin_scholarship_opportunities'))

# ==================== BOURSE PUBLIQUE ====================
@app.route('/bourse-etudes')
def bourse_etudes():
    opportunities = get_all_scholarship_opportunities()
    today = datetime.datetime.now().date().isoformat()
    active_opportunities = [dict(opp) for opp in opportunities if not opp['end_date'] or opp['end_date'] >= today]
    return render_template('bourse_etudes.html', scholarship_opportunities=active_opportunities, today=today)

# ==================== ROUTE DE TEST POUR LES EMAILS ====================
@app.route('/admin/test-email')
@login_required
def admin_test_email():
    """
    Route de test pour vérifier la configuration SMTP.
    Utilisation : /admin/test-email?email=destinataire@exemple.com
    """
    to_email = request.args.get('email') or Config.MAIL_USERNAME
    if not to_email:
        flash("Aucun email de test défini. Utilisez ?email=test@exemple.com", "warning")
        return redirect(url_for('admin_dashboard'))

    test_data = {
        'id': 'TEST',
        'fullname': 'Admin',
        'destination_name': 'Test destination',
        'departure_date': '2026-08-28',
        'travelers': 1
    }
    success = send_confirmation_email(to_email, test_data)
    if success:
        flash(f"Email test envoyé avec succès à {to_email}", "success")
    else:
        flash("Échec de l'envoi du test. Vérifiez les logs du serveur.", "danger")
    return redirect(url_for('admin_dashboard'))

# ==================== ROUTE DE CORRECTION DES IMAGES ====================
@app.route('/admin/fix-images')
@login_required
def admin_fix_images():
    try:
        from models import migrate_image_paths
        count = migrate_image_paths()
        flash(f'{count} chemins d\'images corrigés.', 'success')
    except Exception as e:
        traceback.print_exc()
        flash(f'Erreur lors de la correction : {str(e)}', 'danger')
    return redirect(url_for('admin_destinations'))

# ==================== SÉCURITÉ ====================
SUSPICIOUS_RE = re.compile(r'<\s*(script|iframe|object|embed|svg|img|a)\b|javascript:|on[a-z]+\s*=|data:text/html|union\s+select|drop\s+table|--\s*$|<\?php', re.I)
SCAN_TARGETS = {
    'messages': ['name', 'email', 'phone', 'service', 'message'],
    'bookings': ['fullname', 'email', 'phone', 'destination_name', 'message'],
    'scholarships': ['full_name', 'email', 'phone', 'country', 'study_level', 'field_of_study', 'message'],
    'newsletter': ['email'],
    'destinations': ['name', 'country', 'description', 'image', 'flag_image'],
    'services': ['name', 'description', 'icon', 'image', 'features'],
    'scholarship_opportunities': ['title', 'country', 'description', 'benefits', 'requirements', 'image_url', 'flag_url'],
}


def scan_suspicious_content(limit=200):
    """Repère en base les contenus qui ressemblent à une tentative d'injection."""
    found = []
    conn = get_db()
    try:
        for table, fields in SCAN_TARGETS.items():
            rows = conn.execute(f"SELECT id, {', '.join(fields)} FROM {table}").fetchall()
            for row in rows:
                for field in fields:
                    value = row[field]
                    if isinstance(value, str) and SUSPICIOUS_RE.search(value):
                        found.append({'table': table, 'id': row['id'], 'field': field, 'value': value[:160]})
                        if len(found) >= limit:
                            return found
    finally:
        conn.close()
    return found


@app.route('/admin/securite')
@login_required
def admin_security():
    try:
        backups = security.list_backups()
    except OSError:
        backups = []
    return render_template(
        'admin/securite.html',
        events=security.recent_security_events(100),
        backups=backups,
        suspicious=scan_suspicious_content(),
        totp_enabled=bool(Config.ADMIN_TOTP_SECRET),
        password_hashed=bool(Config.ADMIN_PASSWORD_HASH),
        secret_from_env=bool(os.getenv('SECRET_KEY')),
        https=request.is_secure,
        new_totp=session.pop('new_totp', None),
        new_hash=session.pop('new_hash', None),
    )


@app.route('/admin/securite/sauvegarde', methods=['POST'])
@login_required
def admin_backup_create():
    try:
        path = security.make_backup()
        flash(f'Sauvegarde créée : {os.path.basename(path)}', 'success')
    except Exception as e:
        traceback.print_exc()
        flash(f'Sauvegarde impossible : {e}', 'danger')
    return redirect(url_for('admin_security'))


@app.route('/admin/securite/sauvegarde/<name>')
@login_required
def admin_backup_download(name):
    if not re.fullmatch(r'database-[0-9A-Za-z_-]+\.db', name):
        return redirect(url_for('admin_security'))
    security.log_security_event('sauvegarde téléchargée', request.remote_addr, name)
    return send_from_directory(security.backup_dir(), name, as_attachment=True)


@app.route('/admin/securite/totp', methods=['POST'])
@login_required
def admin_totp_generate():
    secret = security.new_totp_secret()
    session['new_totp'] = {'secret': secret, 'uri': security.totp_uri(secret, Config.ADMIN_USERNAME or 'admin')}
    return redirect(url_for('admin_security') + '#double-authentification')


@app.route('/admin/securite/empreinte', methods=['POST'])
@login_required
def admin_password_hash():
    password = request.form.get('new_password', '')
    if len(password) < 12:
        flash('Choisissez un mot de passe d\'au moins 12 caractères.', 'danger')
        return redirect(url_for('admin_security') + '#mot-de-passe')
    session['new_hash'] = generate_password_hash(password)
    return redirect(url_for('admin_security') + '#mot-de-passe')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_mode = Config.DEBUG
    print("=" * 50)
    print("Kartners Travel Agency - Démarrage")
    print("=" * 50)
    print(f"[INFO] Base de données : {Config.DATABASE}")
    print(f"Site client: http://0.0.0.0:{port}")
    print(f"Admin: http://0.0.0.0:{port}/admin/login")
    print(f"Bourse d'études: http://0.0.0.0:{port}/bourse-etudes")
    print("=" * 50)
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
