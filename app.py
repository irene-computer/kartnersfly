from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_cors import CORS
from config import Config
from models import get_db, init_db
import datetime
import os
import smtplib
import ssl
from email.message import EmailMessage
from werkzeug.utils import secure_filename
import json
import uuid  # <-- AJOUT pour générer des noms uniques

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Configuration des uploads
UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}

# Creer les dossiers s'ils n'existent pas
os.makedirs(os.path.join(UPLOAD_FOLDER, 'flags'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'destinations'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'services'), exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialiser la base de donnees
init_db()


# ==================== FONCTIONS EMAIL ====================

def send_confirmation_email(to_email, booking_data):
    """Envoie un email de confirmation au client depuis kta2k23@gmail.com"""
    try:
        # Configuration SMTP pour Gmail (utilise les variables d'environnement)
        smtp_server = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.environ.get('MAIL_PORT', 587))
        sender_email = os.environ.get('MAIL_USERNAME', 'kta2k23@gmail.com')
        sender_password = os.environ.get('MAIL_PASSWORD', 'Kartners@2025')
        
        # Creer l'email
        msg = EmailMessage()
        msg['Subject'] = f"Confirmation de reservation - KTA-{booking_data['id']}"
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Reply-To'] = sender_email
        
        # Version texte simple
        text_content = f"""
KARTNERS TRAVEL AGENCY
=======================

Bonjour {booking_data['fullname']},

Nous avons le plaisir de vous confirmer votre reservation.

DETAILS DE VOTRE RESERVATION:
- Destination: {booking_data['destination_name']}
- Date de depart: {booking_data['departure_date']}
- Nombre de voyageurs: {booking_data['travelers']}
- Statut: CONFIRMEE

Notre equipe vous contactera prochainement.

Kartners Travel Agency
Tel: +237 676 268 350
Email: kta2k23@gmail.com
Logpom, Douala - Cameroun
        """
        
        # Version HTML
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Confirmation de reservation - Kartners</title>
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #8B5CF6, #3B82F6); color: white; padding: 30px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 24px; }}
                .header p {{ margin: 10px 0 0; opacity: 0.9; }}
                .content {{ padding: 30px; }}
                .info-block {{ background: #f8f9fa; border-radius: 8px; padding: 20px; margin-bottom: 20px; }}
                .info-block h3 {{ margin: 0 0 15px; color: #6B3FA0; }}
                .info-row {{ display: flex; padding: 8px 0; border-bottom: 1px solid #e9ecef; }}
                .info-label {{ width: 130px; font-weight: bold; color: #495057; }}
                .info-value {{ flex: 1; color: #212529; }}
                .status {{ display: inline-block; background: #10B981; color: white; padding: 5px 15px; border-radius: 20px; font-size: 12px; font-weight: bold; }}
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
                    <p>Bonjour <strong>{booking_data['fullname']}</strong>,</p>
                    <p>Nous avons le plaisir de vous confirmer votre reservation de voyage.</p>
                    
                    <div class="info-block">
                        <h3>Details de votre reservation</h3>
                        <div class="info-row">
                            <div class="info-label">Numero :</div>
                            <div class="info-value">KTA-{booking_data['id']}</div>
                        </div>
                        <div class="info-row">
                            <div class="info-label">Destination :</div>
                            <div class="info-value">{booking_data['destination_name']}</div>
                        </div>
                        <div class="info-row">
                            <div class="info-label">Date de depart :</div>
                            <div class="info-value">{booking_data['departure_date']}</div>
                        </div>
                        <div class="info-row">
                            <div class="info-label">Voyageurs :</div>
                            <div class="info-value">{booking_data['travelers']}</div>
                        </div>
                        <div class="info-row">
                            <div class="info-label">Statut :</div>
                            <div class="info-value"><span class="status">CONFIRMEE</span></div>
                        </div>
                    </div>
                    
                    <div class="info-block">
                        <h3>Prochaines etapes</h3>
                        <p>Notre equipe vous contactera dans les prochaines 24-48 heures pour finaliser les details de votre voyage.</p>
                    </div>
                </div>
                <div class="footer">
                    <p>&copy; 2026 Kartners Travel Agency</p>
                    <p>Tel: +237 676 268 350 | Email: kta2k23@gmail.com</p>
                    <p>Logpom, Douala - Cameroun</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Ajouter les deux versions
        msg.set_content(text_content)
        msg.add_alternative(html_content, subtype='html')
        
        # Envoyer l'email
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls(context=context)
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        print(f"[INFO] Email de confirmation envoye a {to_email}")
        return True
        
    except Exception as e:
        print(f"[ERREUR] Envoi email: {str(e)}")
        return False


# ==================== ROUTES CLIENT ====================

@app.route('/')
def home():
    return render_template('index.html')

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
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')


# ==================== ROUTES LEGALES ====================

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
def api_contact():
    """Recoit les messages du formulaire de contact"""
    try:
        data = request.json
        
        if not data.get('name') or not data.get('email') or not data.get('message'):
            return jsonify({'success': False, 'message': 'Veuillez remplir tous les champs requis'}), 400
        
        conn = get_db()
        conn.execute('''
            INSERT INTO messages (name, email, phone, service, message, created_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (data['name'], data['email'], data.get('phone', ''), data.get('service', ''), data['message'], 
              datetime.datetime.now().isoformat(), 'non lu'))
        conn.commit()
        conn.close()
        
        print(f"[INFO] Nouveau message recu de {data['name']}")
        
        return jsonify({'success': True, 'message': 'Merci. Notre equipe vous repondra sous 24h.'})
    except Exception as e:
        print(f"[ERREUR] API contact: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/booking', methods=['POST'])
def api_booking():
    """Recoit les reservations de destinations"""
    try:
        data = request.json
        
        # Validation des champs requis
        required_fields = ['fullname', 'email', 'phone', 'departure_date']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'Le champ {field} est requis'}), 400
        
        conn = get_db()
        
        # Recuperer le nom de la destination
        destination_name = data.get('destination_name', '')
        if not destination_name and data.get('destination_id'):
            dest = conn.execute('SELECT name FROM destinations WHERE id = ?', (data['destination_id'],)).fetchone()
            if dest:
                destination_name = dest['name']
        
        # Insertion dans la base
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO bookings (
                destination_id, destination_name, fullname, email, phone, 
                departure_date, travelers, message, created_at, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('destination_id'),
            destination_name,
            data['fullname'],
            data['email'],
            data['phone'],
            data['departure_date'],
            data.get('travelers', 1),
            data.get('message', ''),
            datetime.datetime.now().isoformat(),
            'en attente'
        ))
        
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        
        return jsonify({'success': True, 'message': 'Reservation envoyee. Nous vous contacterons.', 'id': last_id})
        
    except Exception as e:
        print(f"[ERREUR] API booking: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/newsletter', methods=['POST'])
def api_newsletter():
    """Inscription a la newsletter"""
    try:
        data = request.json
        email = data.get('email')
        
        if not email:
            return jsonify({'success': False, 'message': 'Email requis'}), 400
        
        conn = get_db()
        conn.execute('INSERT OR IGNORE INTO newsletter (email, created_at) VALUES (?, ?)',
                    (email, datetime.datetime.now().isoformat()))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Inscription reussie a la newsletter.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== ADMIN AUTHENTIFICATION ====================

def login_required(f):
    def wrapper(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == Config.ADMIN_USERNAME and password == Config.ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin/login.html', error='Identifiants incorrects')
    return render_template('admin/login.html')


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))


# ==================== ADMIN DASHBOARD ====================

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
    
    # Derniers messages pour le dashboard
    derniers_messages = conn.execute('SELECT * FROM messages ORDER BY created_at DESC LIMIT 5').fetchall()
    
    conn.close()
    
    return render_template('admin/dashboard.html', 
                         messages_non_lus=messages_non_lus,
                         messages_total=messages_total,
                         bookings_en_attente=bookings_en_attente,
                         bookings_total=bookings_total,
                         destinations_count=destinations_count,
                         services_count=services_count,
                         newsletter_count=newsletter_count,
                         derniers_messages=derniers_messages)


# ==================== ADMIN MESSAGES ====================

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
    return redirect(url_for('admin_messages'))


@app.route('/admin/message/delete/<int:id>')
@login_required
def admin_message_delete(id):
    conn = get_db()
    conn.execute('DELETE FROM messages WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_messages'))


# ==================== ADMIN DESTINATIONS ====================

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
        name = request.form.get('name')
        country = request.form.get('country')
        description = request.form.get('description')
        price = float(request.form.get('price'))
        continent = request.form.get('continent', 'europe')
        
        flag_file = request.files.get('flag_image')
        flag_filename = 'flags/default.png'
        if flag_file and allowed_file(flag_file.filename):
            flag_filename_secure = secure_filename(f"flag_{name.lower()}_{flag_file.filename}")
            flag_file.save(os.path.join(UPLOAD_FOLDER, 'flags', flag_filename_secure))
            flag_filename = f"flags/{flag_filename_secure}"
        
        dest_file = request.files.get('destination_image')
        dest_filename = 'destinations/default.jpg'
        if dest_file and allowed_file(dest_file.filename):
            dest_filename_secure = secure_filename(f"dest_{name.lower()}_{dest_file.filename}")
            dest_file.save(os.path.join(UPLOAD_FOLDER, 'destinations', dest_filename_secure))
            dest_filename = f"destinations/{dest_filename_secure}"
        
        conn = get_db()
        conn.execute('''
            INSERT INTO destinations (name, country, flag_image, description, price, image, continent)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, country, flag_filename, description, price, dest_filename, continent))
        conn.commit()
        conn.close()
        
        return redirect(url_for('admin_destinations'))
    except Exception as e:
        return f"Erreur: {str(e)}", 500


@app.route('/admin/destination/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_destination_edit(id):
    conn = get_db()
    
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            country = request.form.get('country')
            description = request.form.get('description')
            price = float(request.form.get('price'))
            continent = request.form.get('continent', 'europe')
            
            old = conn.execute('SELECT flag_image, image FROM destinations WHERE id = ?', (id,)).fetchone()
            
            flag_file = request.files.get('flag_image')
            flag_filename = old['flag_image'] if old else 'flags/default.png'
            if flag_file and allowed_file(flag_file.filename):
                flag_filename_secure = secure_filename(f"flag_{name.lower()}_{flag_file.filename}")
                flag_file.save(os.path.join(UPLOAD_FOLDER, 'flags', flag_filename_secure))
                flag_filename = f"flags/{flag_filename_secure}"
            
            dest_file = request.files.get('destination_image')
            dest_filename = old['image'] if old else 'destinations/default.jpg'
            if dest_file and allowed_file(dest_file.filename):
                dest_filename_secure = secure_filename(f"dest_{name.lower()}_{dest_file.filename}")
                dest_file.save(os.path.join(UPLOAD_FOLDER, 'destinations', dest_filename_secure))
                dest_filename = f"destinations/{dest_filename_secure}"
            
            conn.execute('''
                UPDATE destinations 
                SET name = ?, country = ?, flag_image = ?, description = ?, price = ?, image = ?, continent = ?
                WHERE id = ?
            ''', (name, country, flag_filename, description, price, dest_filename, continent, id))
            conn.commit()
            
            return redirect(url_for('admin_destinations'))
        except Exception as e:
            return f"Erreur: {str(e)}", 500
    else:
        destination = conn.execute('SELECT * FROM destinations WHERE id = ?', (id,)).fetchone()
        conn.close()
        return render_template('admin/destination_edit.html', destination=destination)


@app.route('/admin/destination/delete/<int:id>')
@login_required
def admin_destination_delete(id):
    conn = get_db()
    conn.execute('DELETE FROM destinations WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_destinations'))


# ==================== ADMIN SERVICES (CORRIGE) ====================

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
            name = request.form.get('name')
            description = request.form.get('description')
            icon = request.form.get('icon')
            features = request.form.get('features', '')
            
            # Gestion de l'image
            image_filename = 'services/default.jpg'
            image_file = request.files.get('image')
            if image_file and allowed_file(image_file.filename):
                # Nom unique pour éviter les conflits
                unique_name = f"{uuid.uuid4().hex}_{secure_filename(image_file.filename)}"
                file_path = os.path.join(UPLOAD_FOLDER, 'services', unique_name)
                image_file.save(file_path)
                image_filename = f"services/{unique_name}"
            
            conn = get_db()
            conn.execute('''
                INSERT INTO services (name, description, icon, image, features)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, description, icon, image_filename, features))
            conn.commit()
            conn.close()
            
            flash('Service ajouté avec succès !', 'success')
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
            name = request.form.get('name')
            description = request.form.get('description')
            icon = request.form.get('icon')
            features = request.form.get('features', '')
            
            # Vérifier si l'image doit être supprimée
            remove_image = request.form.get('remove_image') == 'on'
            
            # Gestion de la nouvelle image
            image_file = request.files.get('image')
            image_filename = service['image']  # Garder l'ancienne par défaut
            
            if remove_image:
                # Supprimer l'image actuelle
                if service['image'] and service['image'] != 'services/default.jpg':
                    old_path = os.path.join(UPLOAD_FOLDER, service['image'])
                    if os.path.exists(old_path):
                        try:
                            os.remove(old_path)
                        except:
                            pass
                image_filename = 'services/default.jpg'
            
            if image_file and allowed_file(image_file.filename):
                # Supprimer l'ancienne image si ce n'est pas la default
                if service['image'] and service['image'] != 'services/default.jpg' and not remove_image:
                    old_path = os.path.join(UPLOAD_FOLDER, service['image'])
                    if os.path.exists(old_path):
                        try:
                            os.remove(old_path)
                        except:
                            pass
                
                # Sauvegarder la nouvelle
                unique_name = f"{uuid.uuid4().hex}_{secure_filename(image_file.filename)}"
                file_path = os.path.join(UPLOAD_FOLDER, 'services', unique_name)
                image_file.save(file_path)
                image_filename = f"services/{unique_name}"
            
            # Mettre à jour la base de données
            conn.execute('''
                UPDATE services 
                SET name = ?, description = ?, icon = ?, image = ?, features = ?
                WHERE id = ?
            ''', (name, description, icon, image_filename, features, id))
            conn.commit()
            
            flash('Service mis à jour avec succès !', 'success')
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
    
    # Supprimer l'image associée
    if service and service['image'] and service['image'] != 'services/default.jpg':
        old_path = os.path.join(UPLOAD_FOLDER, service['image'])
        if os.path.exists(old_path):
            try:
                os.remove(old_path)
            except:
                pass
    
    conn.execute('DELETE FROM services WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    
    flash('Service supprimé avec succès !', 'success')
    return redirect(url_for('admin_services'))


# ==================== ADMIN BOOKINGS ====================

@app.route('/admin/bookings')
@login_required
def admin_bookings():
    conn = get_db()
    bookings = conn.execute('''
        SELECT b.*, d.name as dest_name 
        FROM bookings b 
        LEFT JOIN destinations d ON b.destination_id = d.id 
        ORDER BY b.created_at DESC
    ''').fetchall()
    conn.close()
    return render_template('admin/bookings.html', bookings=bookings)


@app.route('/admin/booking/confirm/<int:id>')
@login_required
def admin_booking_confirm(id):
    """Confirmer une reservation et envoyer email au client"""
    conn = get_db()
    
    booking = conn.execute('SELECT * FROM bookings WHERE id = ?', (id,)).fetchone()
    
    if booking:
        # Mettre a jour le statut
        conn.execute('UPDATE bookings SET status = "confirmee" WHERE id = ?', (id,))
        conn.commit()
        
        # Preparer les donnees pour l'email
        booking_data = {
            'id': booking['id'],
            'fullname': booking['fullname'],
            'destination_name': booking['destination_name'],
            'departure_date': booking['departure_date'],
            'travelers': booking['travelers']
        }
        
        # Envoyer l'email de confirmation
        email_sent = send_confirmation_email(booking['email'], booking_data)
        
        if email_sent:
            flash('Reservation confirmee et email envoye au client', 'success')
        else:
            flash('Reservation confirmee mais email non envoye (erreur technique)', 'warning')
    else:
        flash('Reservation non trouvee', 'danger')
    
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
    return redirect(url_for('admin_bookings'))


@app.route('/admin/booking/delete/<int:id>')
@login_required
def admin_booking_delete(id):
    conn = get_db()
    conn.execute('DELETE FROM bookings WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_bookings'))


# ==================== CONTEXTE POUR TEMPLATES ====================

@app.context_processor
def utility_processor():
    def now():
        return datetime.datetime.now()
    return dict(now=now)


# ==================== LANCEMENT POUR RENDER ====================

if __name__ == '__main__':
    # Pour Render, on utilise le port fourni par l'environnement
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('DEBUG', 'False') == 'True'
    
    print("=" * 50)
    print("Kartners Travel Agency - Demarrage")
    print("=" * 50)
    print(f"Site client: http://0.0.0.0:{port}")
    print(f"Admin: http://0.0.0.0:{port}/admin/login")
    print(f"Mode debug: {debug_mode}")
    print("=" * 50)
    app.run(debug=debug_mode, host='0.0.0.0', port=port)