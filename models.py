import sqlite3
from datetime import datetime, timedelta
from config import Config
import os
import re
from werkzeug.utils import secure_filename

# ============================================================
# CONFIGURATION DE LA BASE DE DONNEES
# ============================================================

# Chemin absolu vers la base de données (depuis Config)
DB_PATH = Config.DATABASE

def get_db():
    """
    Retourne une connexion à la base de données.
    - Crée automatiquement le dossier parent s'il n'existe pas.
    - En cas d'échec, utilise un fallback dans le répertoire courant.
    - Affiche des logs pour faciliter le débogage.
    """
    global DB_PATH

    # Tentative de création du dossier parent
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        try:
            os.makedirs(db_dir, exist_ok=True)
            print(f"[INFO] Dossier créé ou existant : {db_dir}")
        except Exception as e:
            print(f"[ERREUR] Impossible de créer {db_dir}: {e}")
            # Fallback vers le répertoire courant
            DB_PATH = 'database.db'
            print(f"[INFO] Fallback vers le répertoire courant : {DB_PATH}")

    # Tentative de connexion
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        print(f"[INFO] Connexion réussie à {DB_PATH}")
        return conn
    except sqlite3.OperationalError as e:
        print(f"[ERREUR] Connexion échouée à {DB_PATH}: {e}")
        # Second fallback : utiliser le répertoire courant
        fallback_path = 'database.db'
        print(f"[INFO] Fallback vers {fallback_path}")
        try:
            conn = sqlite3.connect(fallback_path)
            conn.row_factory = sqlite3.Row
            print(f"[INFO] Connexion réussie à {fallback_path}")
            return conn
        except sqlite3.OperationalError as e2:
            raise RuntimeError(f"Impossible de se connecter à la base de données: {e2}")

# ============================================================
# INITIALISATION DE LA BASE DE DONNEES
# ============================================================

def init_db():
    """Initialise toutes les tables de la base de données."""
    print("[INFO] Initialisation de la base de données...")
    conn = get_db()
    cursor = conn.cursor()

    # --- Table des messages de contact ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            service TEXT,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'non lu'
        )
    ''')

    # --- Table des destinations ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS destinations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            country TEXT NOT NULL,
            flag_image TEXT,
            description TEXT,
            price REAL,
            image TEXT,
            continent TEXT DEFAULT 'europe',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # --- Table des services ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            icon TEXT,
            image TEXT,
            features TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # --- Table des réservations (bookings) ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            destination_id INTEGER,
            destination_name TEXT,
            fullname TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            departure_date TEXT,
            travelers INTEGER DEFAULT 1,
            message TEXT,
            status TEXT DEFAULT 'en attente',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (destination_id) REFERENCES destinations(id)
        )
    ''')

    # --- Table newsletter ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS newsletter (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # --- Table des demandes de bourse (scholarships) ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scholarships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            country TEXT NOT NULL,
            study_level TEXT NOT NULL,
            field_of_study TEXT NOT NULL,
            message TEXT,
            status TEXT DEFAULT 'en attente',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # --- Table des opportunités de bourse ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scholarship_opportunities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            country TEXT NOT NULL,
            study_level TEXT NOT NULL,
            field_of_study TEXT NOT NULL,
            start_date DATE,
            end_date DATE,
            flag_url TEXT,
            image_url TEXT,
            description TEXT,
            benefits TEXT,
            requirements TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # --- Insertion des destinations par défaut ---
    cursor.execute("SELECT COUNT(*) FROM destinations")
    if cursor.fetchone()[0] == 0:
        default_destinations = [
            ('Paris', 'France', 'flags/france.png', 'La ville des lumieres et de l\'amour', 850, 'destinations/paris.jpg', 'europe'),
            ('Dubai', 'Emirats Arabes Unis', 'flags/uae.png', 'Luxe moderne et desert', 1200, 'destinations/dubai.jpg', 'asie'),
            ('Marrakech', 'Maroc', 'flags/morocco.png', 'La perle du Sud', 650, 'destinations/marrakech.jpg', 'afrique'),
            ('Maldives', 'Maldives', 'flags/maldives.png', 'Lagons turquoise et villas sur l\'eau', 2890, 'destinations/maldives.jpg', 'asie'),
            ('Rome', 'Italie', 'flags/italy.png', 'La ville eternelle', 1590, 'destinations/italy.jpg', 'europe'),
            ('Tokyo', 'Japon', 'flags/japan.png', 'Entre tradition et modernite', 3250, 'destinations/japan.jpg', 'asie'),
            ('New York', 'Etats-Unis', 'flags/usa.png', 'La ville qui ne dort jamais', 1990, 'destinations/newyork.jpg', 'amerique'),
            ('Londres', 'Royaume-Uni', 'flags/uk.png', 'La capitale britannique', 1450, 'destinations/london.jpg', 'europe'),
            ('Montreal', 'Canada', 'flags/canada.png', 'Grands espaces et nature sauvage', 2450, 'destinations/canada.jpg', 'amerique'),
            ('Zurich', 'Suisse', 'flags/switzerland.png', 'Alpes, chocolat et precision', 2200, 'destinations/switzerland.jpg', 'europe'),
            ('Istanbul', 'Turquie', 'flags/turkey.png', 'Ou l\'Orient rencontre l\'Occident', 1490, 'destinations/turkey.jpg', 'asie'),
            ('Athenes', 'Grece', 'flags/greece.png', 'Iles paradisiaques et histoire', 1690, 'destinations/greece.jpg', 'europe'),
            ('Dakar', 'Senegal', 'flags/senegal.png', 'La perle de l\'Afrique de l\'Ouest', 890, 'destinations/dakar.jpg', 'afrique'),
            ('Le Caire', 'Egypte', 'flags/egypt.png', 'Les pyramides et la civilisation antique', 1350, 'destinations/egypt.jpg', 'afrique'),
            ('Bali', 'Indonesie', 'flags/indonesia.png', 'Ile des dieux et paradis tropical', 1850, 'destinations/bali.jpg', 'asie'),
            ('Sydney', 'Australie', 'flags/australia.png', 'Opera, plages et kangourous', 3200, 'destinations/australia.jpg', 'oceanie'),
        ]
        cursor.executemany('''
            INSERT INTO destinations (name, country, flag_image, description, price, image, continent) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', default_destinations)

    # --- Insertion des services par défaut ---
    cursor.execute("SELECT COUNT(*) FROM services")
    if cursor.fetchone()[0] == 0:
        default_services = [
            ('Billeterie aerienne', 'Vols nationaux et internationaux aux meilleurs prix', 'fas fa-plane-departure', 'services/airline.jpg', 'Vols nationaux|Tarifs competitis|Reservation rapide'),
            ('Reservation hotels', 'Sejours nationaux et internationaux', 'fas fa-hotel', 'services/hotel.jpg', 'Hotels standards|Confort superieur|Luxe et prestige'),
            ('Assistance visa', 'Tous types de visas pour le monde entier', 'fas fa-passport', 'services/visa.jpg', 'Etudes|Tourisme|Affaires|Suivi complet'),
            ('Pre-enrolement', 'Passeport - Carte Nationale d\'Identite (CNI)', 'fas fa-id-card', 'services/passport.jpg', 'Passeport|CNI|Demarches simplifiees'),
            ('Planification de voyage', 'Voyages organises - Circuits personnalises', 'fas fa-map-marked-alt', 'services/planning.jpg', 'Voyages organises|Circuits personnalises|Sejours thematiques'),
            ('Assurance voyage', 'Couverture complete et securisee', 'fas fa-shield-alt', 'services/insurance.jpg', 'Annulation|Rapatriement|Sante a l\'etranger|Bagages'),
        ]
        cursor.executemany('''
            INSERT INTO services (name, description, icon, image, features) 
            VALUES (?, ?, ?, ?, ?)
        ''', default_services)

    conn.commit()
    conn.close()
    print("[SUCCES] Base de données initialisée avec succès")
    print(f"[SUCCES] Chemin utilisé : {DB_PATH}")

# ============================================================
# FONCTIONS POUR LES MESSAGES
# ============================================================

def add_message(name, email, phone, service, message):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO messages (name, email, phone, service, message, created_at, status)
        VALUES (?, ?, ?, ?, ?, ?, 'non lu')
    ''', (name, email, phone, service, message, datetime.now().isoformat()))
    conn.commit()
    last_id = cursor.lastrowid
    conn.close()
    return last_id

def get_all_messages():
    conn = get_db()
    messages = conn.execute('SELECT * FROM messages ORDER BY created_at DESC').fetchall()
    conn.close()
    return messages

def get_unread_messages_count():
    conn = get_db()
    count = conn.execute('SELECT COUNT(*) FROM messages WHERE status = "non lu"').fetchone()[0]
    conn.close()
    return count

def mark_message_as_read(message_id):
    conn = get_db()
    conn.execute('UPDATE messages SET status = "lu" WHERE id = ?', (message_id,))
    conn.commit()
    conn.close()

def delete_message(message_id):
    conn = get_db()
    conn.execute('DELETE FROM messages WHERE id = ?', (message_id,))
    conn.commit()
    conn.close()

# ============================================================
# FONCTIONS POUR LES DESTINATIONS
# ============================================================

def get_all_destinations():
    conn = get_db()
    destinations = conn.execute('SELECT * FROM destinations ORDER BY name').fetchall()
    conn.close()
    return destinations

def get_destination_by_id(destination_id):
    conn = get_db()
    destination = conn.execute('SELECT * FROM destinations WHERE id = ?', (destination_id,)).fetchone()
    conn.close()
    return destination

def add_destination(name, country, flag_image, description, price, image, continent='europe'):
    conn = get_db()
    conn.execute('''
        INSERT INTO destinations (name, country, flag_image, description, price, image, continent)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (name, country, flag_image, description, price, image, continent))
    conn.commit()
    conn.close()

def update_destination(destination_id, name, country, flag_image, description, price, image, continent):
    conn = get_db()
    conn.execute('''
        UPDATE destinations 
        SET name = ?, country = ?, flag_image = ?, description = ?, price = ?, image = ?, continent = ?
        WHERE id = ?
    ''', (name, country, flag_image, description, price, image, continent, destination_id))
    conn.commit()
    conn.close()

def delete_destination(destination_id):
    conn = get_db()
    conn.execute('DELETE FROM destinations WHERE id = ?', (destination_id,))
    conn.commit()
    conn.close()

def get_destinations_count():
    conn = get_db()
    count = conn.execute('SELECT COUNT(*) FROM destinations').fetchone()[0]
    conn.close()
    return count

# ============================================================
# FONCTIONS POUR LES SERVICES
# ============================================================

def get_all_services():
    conn = get_db()
    services = conn.execute('SELECT * FROM services ORDER BY name').fetchall()
    conn.close()
    return services

def add_service(name, description, icon, image, features=''):
    conn = get_db()
    conn.execute('''
        INSERT INTO services (name, description, icon, image, features)
        VALUES (?, ?, ?, ?, ?)
    ''', (name, description, icon, image, features))
    conn.commit()
    conn.close()

def update_service(service_id, name, description, icon, features):
    conn = get_db()
    conn.execute('''
        UPDATE services 
        SET name = ?, description = ?, icon = ?, features = ?
        WHERE id = ?
    ''', (name, description, icon, features, service_id))
    conn.commit()
    conn.close()

def update_service_image(service_id, image):
    conn = get_db()
    conn.execute('UPDATE services SET image = ? WHERE id = ?', (image, service_id))
    conn.commit()
    conn.close()

def delete_service(service_id):
    conn = get_db()
    conn.execute('DELETE FROM services WHERE id = ?', (service_id,))
    conn.commit()
    conn.close()

def get_services_count():
    conn = get_db()
    count = conn.execute('SELECT COUNT(*) FROM services').fetchone()[0]
    conn.close()
    return count

# ============================================================
# FONCTIONS POUR LES RESERVATIONS
# ============================================================

def add_booking(destination_id, destination_name, fullname, email, phone, departure_date, travelers, message):
    conn = get_db()
    conn.execute('''
        INSERT INTO bookings (destination_id, destination_name, fullname, email, phone, 
                              departure_date, travelers, message, created_at, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'en attente')
    ''', (destination_id, destination_name, fullname, email, phone, 
          departure_date, travelers, message, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_all_bookings():
    conn = get_db()
    bookings = conn.execute('''
        SELECT b.*, d.name as dest_name, d.country as dest_country, d.image as dest_image
        FROM bookings b 
        LEFT JOIN destinations d ON b.destination_id = d.id 
        ORDER BY b.created_at DESC
    ''').fetchall()
    conn.close()
    return bookings

def update_booking_status(booking_id, status):
    conn = get_db()
    conn.execute('UPDATE bookings SET status = ? WHERE id = ?', (status, booking_id))
    conn.commit()
    conn.close()

def delete_booking(booking_id):
    conn = get_db()
    conn.execute('DELETE FROM bookings WHERE id = ?', (booking_id,))
    conn.commit()
    conn.close()

def get_pending_bookings_count():
    conn = get_db()
    count = conn.execute('SELECT COUNT(*) FROM bookings WHERE status = "en attente"').fetchone()[0]
    conn.close()
    return count

# ============================================================
# FONCTIONS POUR LA NEWSLETTER
# ============================================================

def subscribe_newsletter(email):
    conn = get_db()
    conn.execute('INSERT OR IGNORE INTO newsletter (email) VALUES (?)', (email,))
    conn.commit()
    conn.close()

def get_newsletter_count():
    conn = get_db()
    count = conn.execute('SELECT COUNT(*) FROM newsletter').fetchone()[0]
    conn.close()
    return count

def get_all_newsletter_emails():
    conn = get_db()
    emails = conn.execute('SELECT email FROM newsletter').fetchall()
    conn.close()
    return [email['email'] for email in emails]

def get_all_user_emails():
    conn = get_db()
    emails = set()
    
    messages = conn.execute('SELECT DISTINCT email FROM messages').fetchall()
    for msg in messages:
        if msg['email']:
            emails.add(msg['email'])
    
    bookings = conn.execute('SELECT DISTINCT email FROM bookings').fetchall()
    for book in bookings:
        if book['email']:
            emails.add(book['email'])
    
    newsletter = conn.execute('SELECT DISTINCT email FROM newsletter').fetchall()
    for nl in newsletter:
        if nl['email']:
            emails.add(nl['email'])
    
    conn.close()
    return list(emails)

# ============================================================
# FONCTIONS POUR LES BOURSES (DEMANDES)
# ============================================================

def add_scholarship(full_name, email, phone, country, study_level, field_of_study, message):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO scholarships (full_name, email, phone, country, study_level, field_of_study, message, created_at, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'en attente')
    ''', (full_name, email, phone, country, study_level, field_of_study, message, datetime.now().isoformat()))
    conn.commit()
    last_id = cursor.lastrowid
    conn.close()
    return last_id

def get_all_scholarships():
    conn = get_db()
    scholarships = conn.execute('SELECT * FROM scholarships ORDER BY created_at DESC').fetchall()
    conn.close()
    return scholarships

def get_pending_scholarships_count():
    conn = get_db()
    count = conn.execute('SELECT COUNT(*) FROM scholarships WHERE status = "en attente"').fetchone()[0]
    conn.close()
    return count

def update_scholarship_status(scholarship_id, status):
    conn = get_db()
    conn.execute('UPDATE scholarships SET status = ? WHERE id = ?', (status, scholarship_id))
    conn.commit()
    conn.close()

def delete_scholarship(scholarship_id):
    conn = get_db()
    conn.execute('DELETE FROM scholarships WHERE id = ?', (scholarship_id,))
    conn.commit()
    conn.close()

def get_scholarship_by_id(scholarship_id):
    conn = get_db()
    scholarship = conn.execute('SELECT * FROM scholarships WHERE id = ?', (scholarship_id,)).fetchone()
    conn.close()
    return scholarship

def get_scholarships_ending_soon(days=5):
    conn = get_db()
    today = datetime.now().date()
    start_date = (today - timedelta(days=days+5)).isoformat()
    end_date = (today - timedelta(days=days)).isoformat()
    
    scholarships = conn.execute('''
        SELECT * FROM scholarships 
        WHERE created_at BETWEEN ? AND ?
        AND status = "en attente"
    ''', (start_date, end_date)).fetchall()
    
    conn.close()
    return scholarships

# ============================================================
# FONCTIONS POUR LES OPPORTUNITES DE BOURSE
# ============================================================

def add_scholarship_opportunity(title, country, study_level, field_of_study,
                                start_date, end_date,
                                flag_url, image_url,
                                description, benefits, requirements):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO scholarship_opportunities 
        (title, country, study_level, field_of_study, start_date, end_date,
         flag_url, image_url, description, benefits, requirements, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (title, country, study_level, field_of_study,
          start_date, end_date,
          flag_url, image_url,
          description, benefits, requirements,
          datetime.now().isoformat()))
    conn.commit()
    last_id = cursor.lastrowid
    conn.close()
    return last_id

def update_scholarship_opportunity(opportunity_id, title, country, study_level,
                                   field_of_study, start_date, end_date,
                                   flag_url, image_url,
                                   description, benefits, requirements):
    conn = get_db()
    conn.execute('''
        UPDATE scholarship_opportunities 
        SET title = ?, country = ?, study_level = ?, field_of_study = ?,
            start_date = ?, end_date = ?, flag_url = ?, image_url = ?,
            description = ?, benefits = ?, requirements = ?
        WHERE id = ?
    ''', (title, country, study_level, field_of_study,
          start_date, end_date,
          flag_url, image_url,
          description, benefits, requirements,
          opportunity_id))
    conn.commit()
    conn.close()

def get_all_scholarship_opportunities():
    conn = get_db()
    opportunities = conn.execute('SELECT * FROM scholarship_opportunities ORDER BY created_at DESC').fetchall()
    conn.close()
    return opportunities

def get_scholarship_opportunity_by_id(opportunity_id):
    conn = get_db()
    opportunity = conn.execute('SELECT * FROM scholarship_opportunities WHERE id = ?', (opportunity_id,)).fetchone()
    conn.close()
    return opportunity

def delete_scholarship_opportunity(opportunity_id):
    conn = get_db()
    conn.execute('DELETE FROM scholarship_opportunities WHERE id = ?', (opportunity_id,))
    conn.commit()
    conn.close()

# ============================================================
# FONCTIONS DE MIGRATION / CORRECTION DES CHEMINS
# ============================================================

def migrate_image_paths():
    conn = get_db()
    cursor = conn.cursor()
    
    opportunities = cursor.execute('SELECT id, flag_url, image_url FROM scholarship_opportunities').fetchall()
    
    updated = 0
    for opp in opportunities:
        updates = {}
        for field in ['flag_url', 'image_url']:
            val = opp[field]
            if val and not val.startswith('http') and not val.startswith('images/'):
                updates[field] = f"images/{val}"
        if updates:
            sql = "UPDATE scholarship_opportunities SET "
            set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
            values = list(updates.values()) + [opp['id']]
            cursor.execute(f"UPDATE scholarship_opportunities SET {set_clause} WHERE id = ?", values)
            updated += 1
    
    conn.commit()
    conn.close()
    print(f"Migration terminée : {updated} enregistrements mis à jour.")
    return updated

# ============================================================
# INITIALISATION DES DOSSIERS D'UPLOAD
# ============================================================

def create_upload_folders():
    folders = [
        'static/images/flags',
        'static/images/destinations',
        'static/images/services',
        'static/images/scholarships'
    ]
    for folder in folders:
        os.makedirs(folder, exist_ok=True)