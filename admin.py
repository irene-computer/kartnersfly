from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from config import Config
from models import get_db, init_db
import datetime
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config.from_object(Config)

# Configuration des uploads
UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Creer les dossiers s'ils n'existent pas
os.makedirs(os.path.join(UPLOAD_FOLDER, 'flags'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'destinations'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'services'), exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Middleware d'authentification
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

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    conn = get_db()
    messages_count = conn.execute('SELECT COUNT(*) FROM messages WHERE status = "non lu"').fetchone()[0]
    bookings_count = conn.execute('SELECT COUNT(*) FROM bookings WHERE status = "en attente"').fetchone()[0]
    destinations_count = conn.execute('SELECT COUNT(*) FROM destinations').fetchone()[0]
    services_count = conn.execute('SELECT COUNT(*) FROM services').fetchone()[0]
    conn.close()
    return render_template('admin/dashboard.html', 
                         messages_count=messages_count,
                         bookings_count=bookings_count,
                         destinations_count=destinations_count,
                         services_count=services_count)

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

@app.route('/admin/destinations')
@login_required
def admin_destinations():
    conn = get_db()
    destinations = conn.execute('SELECT * FROM destinations').fetchall()
    conn.close()
    return render_template('admin/destinations_admin.html', destinations=destinations)

@app.route('/admin/destination/add', methods=['POST'])
@login_required
def admin_destination_add():
    try:
        name = request.form.get('name')
        country = request.form.get('country')
        description = request.form.get('description')
        price = float(request.form.get('price'))
        
        # Upload du drapeau
        flag_file = request.files.get('flag_image')
        flag_filename = 'flags/default.png'
        if flag_file and allowed_file(flag_file.filename):
            flag_filename_secure = secure_filename(f"flag_{name.lower()}_{flag_file.filename}")
            flag_file.save(os.path.join(UPLOAD_FOLDER, 'flags', flag_filename_secure))
            flag_filename = f"flags/{flag_filename_secure}"
        
        # Upload de l'image destination
        dest_file = request.files.get('destination_image')
        dest_filename = 'destinations/default.jpg'
        if dest_file and allowed_file(dest_file.filename):
            dest_filename_secure = secure_filename(f"dest_{name.lower()}_{dest_file.filename}")
            dest_file.save(os.path.join(UPLOAD_FOLDER, 'destinations', dest_filename_secure))
            dest_filename = f"destinations/{dest_filename_secure}"
        
        conn = get_db()
        conn.execute('''
            INSERT INTO destinations (name, country, flag_image, description, price, image) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, country, flag_filename, description, price, dest_filename))
        conn.commit()
        conn.close()
        
        return redirect(url_for('admin_destinations'))
    except Exception as e:
        return f"Erreur: {str(e)}", 500

@app.route('/admin/destination/delete/<int:id>')
@login_required
def admin_destination_delete(id):
    conn = get_db()
    conn.execute('DELETE FROM destinations WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_destinations'))

@app.route('/admin/services')
@login_required
def admin_services():
    conn = get_db()
    services = conn.execute('SELECT * FROM services').fetchall()
    conn.close()
    return render_template('admin/services_admin.html', services=services)

@app.route('/admin/service/add', methods=['POST'])
@login_required
def admin_service_add():
    try:
        name = request.form.get('name')
        description = request.form.get('description')
        icon = request.form.get('icon')
        
        conn = get_db()
        conn.execute('INSERT INTO services (name, description, icon) VALUES (?, ?, ?)',
                    (name, description, icon))
        conn.commit()
        conn.close()
        
        return redirect(url_for('admin_services'))
    except Exception as e:
        return f"Erreur: {str(e)}", 500

@app.route('/admin/service/delete/<int:id>')
@login_required
def admin_service_delete(id):
    conn = get_db()
    conn.execute('DELETE FROM services WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_services'))

@app.route('/admin/bookings')
@login_required
def admin_bookings():
    conn = get_db()
    bookings = conn.execute('''
        SELECT b.*, d.name as destination_name 
        FROM bookings b 
        LEFT JOIN destinations d ON b.destination_id = d.id 
        ORDER BY b.created_at DESC
    ''').fetchall()
    conn.close()
    return render_template('admin/bookings.html', bookings=bookings)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)