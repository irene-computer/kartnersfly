from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, Response
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from config import Config
from models import get_db, init_db
import datetime
import os
import smtplib
import ssl
from email.message import EmailMessage
from werkzeug.utils import secure_filename
import json
import uuid
import re
import csv
from io import StringIO
import secrets
from functools import wraps

# ============================================================
# CORRECTION ROBUSTE DE LA BASE DE DONNÉES
# ============================================================
import tempfile

# S'assurer que le chemin de la base est absolu et résolu
db_path_original = Config.DATABASE
db_dir = os.path.dirname(db_path_original)

# Si le dossier parent n'existe pas ou n'est pas accessible, on utilise un fallback
try:
    if db_dir:
        os.makedirs(db_dir, exist_ok=True, mode=0o777)
        # Tester l'écriture
        test_file = os.path.join(db_dir, '.write_test')
        with open(test_file, 'w') as f:
            f.write('ok')
        os.remove(test_file)
        print(f"[OK] Dossier de la base accessible : {db_dir}")
    else:
        # Pas de dossier parent, on est dans le répertoire courant
        print("[INFO] Base de données dans le répertoire courant.")
except Exception as e:
    print(f"[ERREUR] Impossible d'utiliser {db_dir} : {e}")
    # Fallback vers /tmp (toujours accessible en écriture)
    fallback_dir = tempfile.gettempdir()
    fallback_path = os.path.join(fallback_dir, 'database.db')
    Config.DATABASE = fallback_path
    print(f"[INFO] Utilisation du fallback : {Config.DATABASE}")
    # Créer le dossier /tmp si besoin (existe toujours)
    os.makedirs(fallback_dir, exist_ok=True)

# ============================================================
# IMPORTS DES FONCTIONS MODELS
# ============================================================
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
    update_scholarship_opportunity
)

app = Flask(__name__)
app.config.from_object(Config)

# ==================== SECURITE ====================
app.config['SESSION_COOKIE_SECURE'] = not Config.DEBUG
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=1)

if Config.DEBUG:
    CORS(app)
else:
    CORS(app, resources={r"/api/*": {"origins": "https://www.kartnersagency.com"}})

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

def sanitize_input(data):
    """Nettoie les entrées utilisateur"""
    if isinstance(data, dict):
        return {k: sanitize_input(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_input(item) for item in data]
    elif isinstance(data, str):
        return re.sub(r'[<>"\']', '', data)
    return data

@app.before_request
def before_request_security():
    if request.content_length and request.content_length > 10 * 1024 * 1024:
        return jsonify({'error': 'Request too large'}), 413

    if request.method in ['POST', 'PUT', 'PATCH']:
        if request.content_type and 'multipart/form-data' in request.content_type:
            return None
        if request.content_type and 'application/x-www-form-urlencoded' in request.content_type:
            return None
        if request.content_type and 'application/json' in request.content_type:
            return None
        if not request.content_type:
            return None
        return jsonify({'error': 'Unsupported Media Type'}), 415

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        if session.get('admin_ip') != request.remote_addr:
            session.clear()
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return wrapper

# ==================== UPLOADS ====================
UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}

# Création des sous-dossiers
for sub in ['flags', 'destinations', 'services', 'scholarships']:
    os.makedirs(os.path.join(UPLOAD_FOLDER, sub), exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_image(file, subfolder='scholarships'):
    """
    Sauvegarde une image uploadée et retourne le chemin relatif (ex: images/sous-dossier/nom.jpg)
    Utilisation : save_uploaded_image(request.files['image'], 'destinations')
    """
    if not file or not allowed_file(file.filename):
        return None
    filename = secure_filename(file.filename)
    unique_name = f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}_{filename}"
    folder = os.path.join(UPLOAD_FOLDER, subfolder)  # static/images/sous-dossier
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, unique_name)
    file.save(filepath)
    # Retourne le chemin relatif à utiliser avec url_for('static', filename=...)
    return f"images/{subfolder}/{unique_name}"

# Initialiser la base de données
init_db()

# ==================== CONTEXTE GLOBAL ====================
@app.context_processor
def utility_processor():
    def now():
        return datetime.datetime.now()
    try:
        scholarships_pending = get_pending_scholarships_count()
    except:
        scholarships_pending = 0
    return dict(now=now, scholarships_pending=scholarships_pending)

# ==================== EMAILS ====================
def send_confirmation_email(to_email, booking_data):
    try:
        smtp_server = Config.MAIL_SERVER
        smtp_port = Config.MAIL_PORT
        sender_email = Config.MAIL_USERNAME
        sender_password = Config.MAIL_PASSWORD

        if not sender_email or not sender_password:
            print("[ERREUR] Email non configuré")
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
        """
        msg.set_content(text_content)

        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls(context=context)
            server.login(sender_email, sender_password)
            server.send_message(msg)

        print(f"[INFO] Email de confirmation envoyé à {to_email}")
        return True
    except Exception as e:
        print(f"[ERREUR] Envoi email: {str(e)}")
        return False

def send_bulk_email(recipients, subject, html_content, text_content=None):
    if not recipients:
        return 0, 0
    try:
        smtp_server = Config.MAIL_SERVER
        smtp_port = Config.MAIL_PORT
        sender_email = Config.MAIL_USERNAME
        sender_password = Config.MAIL_PASSWORD

        if not sender_email or not sender_password:
            print("[ERREUR] Email non configuré")
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
                except Exception as e:
                    fail_count += 1
                    print(f"[ERREUR] Envoi à {recipient}: {str(e)}")
        return success_count, fail_count
    except Exception as e:
        print(f"[ERREUR] Envoi de masse: {str(e)}")
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
            </div>
            <div class="footer">
                <p>&copy; 2026 Kartners Travel Agency</p>
                <p>Tel: {Config.PHONE} | Email: {Config.EMAIL}</p>
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
    """

    return send_bulk_email(recipients, subject, html_content, text_content)

# ==================== ROUTES CLIENT ====================
@app.route('/')
def home():
    conn = get_db()
    destinations_list = conn.execute('SELECT * FROM destinations LIMIT 6').fetchall()
    services_list = conn.execute('SELECT * FROM services LIMIT 4').fetchall()
    conn.close()
    return render_template('index.html', destinations=destinations_list, services=services_list)

@app.route('/destinations')
def destinations():
    conn = get_db()
    destinations_list = conn.execute('SELECT * FROM destinations ORDER BY name').fetchall()
    conn.close()
    return render_template('destinations.html', destinations=destinations_list)

@app.route('/services')
def services_page():
    conn = get_db()
    services_list = conn.execute('SELECT * FROM services ORDER BY name').fetchall()
    conn.close()
    return render_template('services.html', services=services_list)

@app.route('/about')
def about():
    conn = get_db()
    services_list = conn.execute('SELECT * FROM services ORDER BY name').fetchall()
    conn.close()
    return render_template('about.html', services=services_list)

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/mentions-legales')
def mentions_legales():
    return render_template('legal/mentions.html')

@app.route('/cgv')
def cgv():
    return render_template('legal/cgv.html')

@app.route('/politique-confidentialite')
def confidentialite():
    return render_template('legal/confidentialite.html')

# ==================== API CLIENT ====================
@app.route('/api/contact', methods=['POST'])
@limiter.limit("5 per minute")
def api_contact():
    try:
        data = request.json
        data = sanitize_input(data)

        if not data.get('name') or not data.get('email') or not data.get('message'):
            return jsonify({'success': False, 'message': 'Champs requis'}), 400

        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', data['email']):
            return jsonify({'success': False, 'message': 'Email invalide'}), 400

        conn = get_db()
        conn.execute('''
            INSERT INTO messages (name, email, phone, service, message, created_at, status)
            VALUES (?, ?, ?, ?, ?, ?, 'non lu')
        ''', (data['name'], data['email'], data.get('phone', ''), data.get('service', ''), data['message'],
              datetime.datetime.now().isoformat()))
        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Merci. Notre équipe vous répondra sous 24h.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/scholarship', methods=['POST'])
@limiter.limit("10 per minute")
def api_scholarship():
    try:
        data = request.get_json()
        data = sanitize_input(data)

        required = ['full_name', 'email', 'country', 'study_level', 'field_of_study']
        for field in required:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'Le champ {field} est requis'}), 400

        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', data['email']):
            return jsonify({'success': False, 'message': 'Email invalide'}), 400

        scholarship_id = add_scholarship(
            full_name=data.get('full_name'),
            email=data.get('email'),
            phone=data.get('phone', ''),
            country=data.get('country'),
            study_level=data.get('study_level'),
            field_of_study=data.get('field_of_study'),
            message=data.get('message', '')
        )

        if scholarship_id:
            return jsonify({'success': True, 'message': 'Votre demande a été envoyée avec succès'})
        else:
            return jsonify({'success': False, 'message': 'Erreur lors de l\'enregistrement'}), 500

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/booking', methods=['POST'])
@limiter.limit("5 per minute")
def api_booking():
    try:
        data = request.json
        data = sanitize_input(data)

        required_fields = ['fullname', 'email', 'phone', 'departure_date']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'Le champ {field} est requis'}), 400

        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', data['email']):
            return jsonify({'success': False, 'message': 'Email invalide'}), 400

        conn = get_db()
        destination_name = data.get('destination_name', '')
        if not destination_name and data.get('destination_id'):
            dest = conn.execute('SELECT name FROM destinations WHERE id = ?', (data['destination_id'],)).fetchone()
            if dest:
                destination_name = dest['name']

        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO bookings (
                destination_id, destination_name, fullname, email, phone,
                departure_date, travelers, message, created_at, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'en attente')
        ''', (
            data.get('destination_id'),
            destination_name,
            data['fullname'],
            data['email'],
            data['phone'],
            data['departure_date'],
            data.get('travelers', 1),
            data.get('message', ''),
            datetime.datetime.now().isoformat()
        ))

        conn.commit()
        last_id = cursor.lastrowid
        conn.close()

        return jsonify({'success': True, 'message': 'Réservation envoyée.', 'id': last_id})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/newsletter', methods=['POST'])
@limiter.limit("10 per minute")
def api_newsletter():
    try:
        data = request.json
        email = data.get('email')

        if not email or not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return jsonify({'success': False, 'message': 'Email invalide'}), 400

        conn = get_db()
        conn.execute('INSERT OR IGNORE INTO newsletter (email, created_at) VALUES (?, ?)',
                    (email, datetime.datetime.now().isoformat()))
        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Inscription réussie.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== ADMIN ====================
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        username = sanitize_input(username)
        password = sanitize_input(password)

        if username == Config.ADMIN_USERNAME and password == Config.ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            session['admin_username'] = username
            session['admin_ip'] = request.remote_addr
            session.permanent = True
            return redirect(url_for('admin_dashboard'))
        else:
            print(f"[SECURITE] Tentative d'accès admin échouée depuis {request.remote_addr}")
            return render_template('admin/login.html', error='Identifiants incorrects')
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    conn = get_db()
    messages_non_lus = conn.execute('SELECT COUNT(*) FROM messages WHERE status = "non lu"').fetchone()[0]
    messages_total = conn.execute('SELECT COUNT(*) FROM messages').fetchone()[0]
    bookings_en_attente = conn.execute('SELECT COUNT(*) FROM bookings WHERE status = "en attente"').fetchone()[0]
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
    conn.execute('UPDATE messages SET status = "lu" WHERE id = ?', (id,))
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

# ========== DESTINATIONS (avec images uniformisées) ==========
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

        # Flag image
        flag_file = request.files.get('flag_image')
        flag_path = save_uploaded_image(flag_file, 'flags') if flag_file else None
        if not flag_path:
            flag_path = 'images/flags/default.png'  # fallback

        # Destination image
        dest_file = request.files.get('destination_image')
        dest_path = save_uploaded_image(dest_file, 'destinations') if dest_file else None
        if not dest_path:
            dest_path = 'images/destinations/default.jpg'

        conn = get_db()
        conn.execute('''
            INSERT INTO destinations (name, country, flag_image, description, price, image, continent)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, country, flag_path, description, price, dest_path, continent))
        conn.commit()
        conn.close()
        flash('Destination ajoutée avec succès', 'success')
        return redirect(url_for('admin_destinations'))
    except Exception as e:
        flash(f'Erreur: {str(e)}', 'danger')
        return redirect(url_for('admin_destinations'))

@app.route('/admin/destination/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_destination_edit(id):
    conn = get_db()
    if request.method == 'POST':
        try:
            name = sanitize_input(request.form.get('name'))
            country = sanitize_input(request.form.get('country'))
            description = sanitize_input(request.form.get('description'))
            price = float(request.form.get('price'))
            continent = sanitize_input(request.form.get('continent', 'europe'))

            old = conn.execute('SELECT flag_image, image FROM destinations WHERE id = ?', (id,)).fetchone()
            flag_path = old['flag_image']
            dest_path = old['image']

            # Nouveau drapeau
            flag_file = request.files.get('flag_image')
            if flag_file and allowed_file(flag_file.filename):
                if flag_path and not flag_path.endswith('default.png'):
                    old_flag = os.path.join(UPLOAD_FOLDER, flag_path.replace('images/', ''))
                    if os.path.exists(old_flag):
                        try: os.remove(old_flag)
                        except: pass
                flag_path = save_uploaded_image(flag_file, 'flags')

            # Nouvelle image destination
            dest_file = request.files.get('destination_image')
            if dest_file and allowed_file(dest_file.filename):
                if dest_path and not dest_path.endswith('default.jpg'):
                    old_dest = os.path.join(UPLOAD_FOLDER, dest_path.replace('images/', ''))
                    if os.path.exists(old_dest):
                        try: os.remove(old_dest)
                        except: pass
                dest_path = save_uploaded_image(dest_file, 'destinations')

            conn.execute('''
                UPDATE destinations
                SET name = ?, country = ?, flag_image = ?, description = ?, price = ?, image = ?, continent = ?
                WHERE id = ?
            ''', (name, country, flag_path, description, price, dest_path, continent, id))
            conn.commit()
            flash('Destination mise à jour avec succès', 'success')
            return redirect(url_for('admin_destinations'))
        except Exception as e:
            flash(f'Erreur: {str(e)}', 'danger')
            return redirect(url_for('admin_destinations'))
    else:
        destination = conn.execute('SELECT * FROM destinations WHERE id = ?', (id,)).fetchone()
        conn.close()
        return render_template('admin/destination_edit.html', destination=destination)

@app.route('/admin/destination/delete/<int:id>')
@login_required
def admin_destination_delete(id):
    conn = get_db()
    dest = conn.execute('SELECT flag_image, image FROM destinations WHERE id = ?', (id,)).fetchone()
    if dest:
        for field in ['flag_image', 'image']:
            val = dest[field]
            if val and not val.endswith(('default.png', 'default.jpg')):
                path = os.path.join(UPLOAD_FOLDER, val.replace('images/', ''))
                if os.path.exists(path):
                    try: os.remove(path)
                    except: pass
    conn.execute('DELETE FROM destinations WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Destination supprimée', 'success')
    return redirect(url_for('admin_destinations'))

# ========== SERVICES (avec images uniformisées) ==========
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

            conn = get_db()
            conn.execute('''
                INSERT INTO services (name, description, icon, image, features)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, description, icon, image_path, features))
            conn.commit()
            conn.close()
            flash('Service ajouté avec succès', 'success')
            return redirect(url_for('admin_services'))
        except Exception as e:
            flash(f'Erreur: {str(e)}', 'danger')
            return redirect(url_for('admin_service_add'))
    return render_template('admin/service_edit.html', service=None)

@app.route('/admin/service/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_service_edit(id):
    conn = get_db()
    service = conn.execute('SELECT * FROM services WHERE id = ?', (id,)).fetchone()
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

            conn.execute('''
                UPDATE services
                SET name = ?, description = ?, icon = ?, image = ?, features = ?
                WHERE id = ?
            ''', (name, description, icon, image_path, features, id))
            conn.commit()
            flash('Service mis à jour avec succès', 'success')
            return redirect(url_for('admin_services'))
        except Exception as e:
            flash(f'Erreur: {str(e)}', 'danger')
    conn.close()
    return render_template('admin/service_edit.html', service=service)

@app.route('/admin/service/delete/<int:id>')
@login_required
def admin_service_delete(id):
    conn = get_db()
    service = conn.execute('SELECT image FROM services WHERE id = ?', (id,)).fetchone()
    if service and service['image'] and not service['image'].endswith('default.jpg'):
        old_path = os.path.join(UPLOAD_FOLDER, service['image'].replace('images/', ''))
        if os.path.exists(old_path):
            try: os.remove(old_path)
            except: pass
    conn.execute('DELETE FROM services WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Service supprimé avec succès', 'success')
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
        conn.execute('UPDATE bookings SET status = "confirmee" WHERE id = ?', (id,))
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
            flash('Réservation confirmée mais email non envoyé (erreur technique)', 'warning')
    else:
        flash('Réservation non trouvée', 'danger')
    conn.close()
    return redirect(url_for('admin_bookings'))

@app.route('/admin/booking/update/<int:id>', methods=['POST'])
@login_required
def admin_booking_update(id):
    status = request.form.get('status')
    conn = get_db()
    conn.execute('UPDATE bookings SET status = ? WHERE id = ?', (status, id))
    conn.commit()
    conn.close()
    flash('Statut mis à jour', 'success')
    return redirect(url_for('admin_bookings'))

@app.route('/admin/booking/delete/<int:id>')
@login_required
def admin_booking_delete(id):
    conn = get_db()
    conn.execute('DELETE FROM bookings WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Réservation supprimée', 'success')
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
    for b in bookings:
        writer.writerow([
            b['id'], b['fullname'], b['email'], b['phone'],
            b['destination_name'] or b['dest_name'],
            b['departure_date'], b['travelers'],
            b['status'], b['created_at']
        ])
    response = Response(output.getvalue(), mimetype='text/csv')
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
                    {content}
                </div>
                <div class="footer">
                    <p>&copy; 2026 Kartners Travel Agency</p>
                    <p>Tel: {Config.PHONE} | Email: {Config.EMAIL}</p>
                </div>
            </div>
        </body>
        </html>
        """
        text_content = re.sub(r'<[^>]+>', '', content)
        success, fail = send_bulk_email(recipients, subject, html_content, text_content)
        flash(f'Newsletter envoyée. {success} emails envoyés, {fail} échecs.', 'success')
        return redirect(url_for('admin_newsletter'))
    except Exception as e:
        flash(f'Erreur: {str(e)}', 'danger')
        return redirect(url_for('admin_newsletter'))

@app.route('/admin/newsletter/delete/<int:id>')
@login_required
def admin_newsletter_delete(id):
    conn = get_db()
    conn.execute('DELETE FROM newsletter WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Abonné supprimé', 'success')
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
        data = request.get_json()
        status = data.get('status')
        if not status:
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

# ========== ADMIN SCHOLARSHIP OPPORTUNITIES (avec images) ==========
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

            # Notification
            scholarship_data = {
                'country': country,
                'study_level': study_level,
                'field_of_study': field_of_study,
                'deadline': end_date or 'Consultez notre site'
            }
            recipients = get_all_user_emails()
            if recipients:
                send_scholarship_notification(recipients, scholarship_data)

            flash('Bourse ajoutée avec succès !', 'success')
            return redirect(url_for('admin_scholarship_opportunities'))
        except Exception as e:
            flash(f'Erreur: {str(e)}', 'danger')
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
            flash(f'Erreur: {str(e)}', 'danger')
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
        flash(f'Erreur: {str(e)}', 'danger')
    return redirect(url_for('admin_scholarship_opportunities'))

# ==================== BOURSE PUBLIQUE ====================
@app.route('/bourse-etudes')
def bourse_etudes():
    opportunities = get_all_scholarship_opportunities()
    today = datetime.datetime.now().date().isoformat()
    active_opportunities = [opp for opp in opportunities if opp['end_date'] is None or opp['end_date'] >= today]
    return render_template('bourse_etudes.html', scholarship_opportunities=active_opportunities, today=today)

# ==================== LANCEMENT ====================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_mode = Config.DEBUG
    print("=" * 50)
    print("Kartners Travel Agency - Démarrage")
    print("=" * 50)
    print(f"[INFO] Base de données initialisée : {Config.DATABASE}")
    print(f"[INFO] Admin : {Config.ADMIN_USERNAME} / {Config.ADMIN_PASSWORD}")
    print("Répertoire de travail :", os.getcwd())
    print(f"Site client: http://0.0.0.0:{port}")
    print(f"Admin: http://0.0.0.0:{port}/admin/login")
    print(f"Bourse d'études: http://0.0.0.0:{port}/bourse-etudes")
    print(f"Mode debug: {debug_mode}")
    print(f"Email configuré: {Config.MAIL_USERNAME}")
    print("=" * 50)
    app.run(debug=debug_mode, host='0.0.0.0', port=port)