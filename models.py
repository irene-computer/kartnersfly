import sqlite3
from datetime import datetime, timedelta
from config import Config
import os
import re
from werkzeug.utils import secure_filename

DB_PATH = Config.DATABASE


def _resolve_db_path():
    """Vérifie une seule fois que le dossier de la base est accessible en écriture."""
    global DB_PATH
    db_dir = os.path.dirname(DB_PATH)
    if not db_dir:
        return
    try:
        os.makedirs(db_dir, exist_ok=True)
        if not os.access(db_dir, os.W_OK):
            raise PermissionError(db_dir)
    except OSError as e:
        DB_PATH = os.path.join('/tmp', 'database.db')
        print(f"[ATTENTION] {db_dir} non accessible ({e}). Base temporaire : {DB_PATH}")


_resolve_db_path()


def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def normalize_image_path(path):
    if not path:
        return path
    path = path.strip()
    if path.startswith(('http://', 'https://')):
        return path
    if path.startswith('images/'):
        return path
    return f"images/{path}"

def init_db():
    print("[INFO] Initialisation de la base de données...")
    conn = get_db()
    try:
        conn.execute('PRAGMA journal_mode = WAL')  # lectures et écritures simultanées (plusieurs workers)
    except sqlite3.OperationalError:
        pass
    cursor = conn.cursor()

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

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS newsletter (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

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

    cursor.execute("SELECT COUNT(*) FROM destinations")
    if cursor.fetchone()[0] == 0:
        # Photos libres de droits (Unsplash, voir static/images/destinations/CREDITS.md).
        # Dakar n'a pas encore de photo : un visuel généré s'affiche. Les
        # drapeaux manquants sont chargés depuis flagcdn.
        default_destinations = [
            ('Paris', 'France', 'images/flags/france.png', "La ville des lumières et de l'amour", 850, 'images/destinations/kta-paris.jpg', 'europe'),
            ('Dubai', 'Émirats Arabes Unis', '', 'Luxe moderne et désert', 1200, 'images/destinations/kta-dubai.jpg', 'asie'),
            ('Marrakech', 'Maroc', '', 'La perle du Sud', 650, 'images/destinations/kta-marrakech.jpg', 'afrique'),
            ('Maldives', 'Maldives', '', "Lagons turquoise et villas sur l'eau", 2890, 'images/destinations/kta-maldives.jpg', 'asie'),
            ('Rome', 'Italie', '', 'La ville éternelle', 1590, 'images/destinations/kta-rome.jpg', 'europe'),
            ('Tokyo', 'Japon', '', 'Entre tradition et modernité', 3250, 'images/destinations/kta-tokyo.jpg', 'asie'),
            ('New York', 'États-Unis', '', 'La ville qui ne dort jamais', 1990, 'images/destinations/kta-new-york.jpg', 'amerique'),
            ('Londres', 'Royaume-Uni', '', 'La capitale britannique', 1450, 'images/destinations/kta-londres.jpg', 'europe'),
            ('Montréal', 'Canada', '', 'Grands espaces et nature sauvage', 2450, 'images/destinations/kta-montreal.jpg', 'amerique'),
            ('Zurich', 'Suisse', 'images/flags/flag_zurich_drapeausuisse.jpeg', 'Alpes, chocolat et précision', 2200, 'images/destinations/dest_zurich_suisse.jpg', 'europe'),
            ('Istanbul', 'Turquie', '', "Où l'Orient rencontre l'Occident", 1490, 'images/destinations/kta-istanbul.jpg', 'asie'),
            ('Athènes', 'Grèce', '', 'Îles paradisiaques et histoire', 1690, 'images/destinations/kta-athenes.jpg', 'europe'),
            ('Dakar', 'Sénégal', '', "La perle de l'Afrique de l'Ouest", 890, '', 'afrique'),
            ('Le Caire', 'Égypte', '', 'Les pyramides et la civilisation antique', 1350, 'images/destinations/kta-le-caire.jpg', 'afrique'),
            ('Bali', 'Indonésie', '', 'Île des dieux et paradis tropical', 1850, 'images/destinations/kta-bali.jpg', 'asie'),
            ('Sydney', 'Australie', '', 'Opéra, plages et kangourous', 3200, 'images/destinations/kta-sydney.jpg', 'oceanie'),
        ]
        cursor.executemany('''
            INSERT INTO destinations (name, country, flag_image, description, price, image, continent) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', default_destinations)

    cursor.execute("SELECT COUNT(*) FROM services")
    if cursor.fetchone()[0] == 0:
        default_services = [
            ('Billetterie aérienne', 'Vols nationaux et internationaux aux meilleurs prix', 'fas fa-plane-departure', 'images/services/airline.jpg', 'Vols nationaux et internationaux|Tarifs compétitifs|Réservation rapide'),
            ('Réservation hôtelière', 'Séjours nationaux et internationaux', 'fas fa-hotel', 'images/services/hotel.jpg', 'Hôtels standards|Confort supérieur|Luxe et prestige'),
            ('Assistance visa', 'Tous types de visas pour le monde entier', 'fas fa-passport', 'images/services/visa.jpg', 'Études|Tourisme|Affaires|Suivi complet'),
            ('Pré-enrôlement', "Passeport - Carte nationale d'identité (CNI)", 'fas fa-id-card', 'images/services/passport.jpg', 'Passeport|CNI|Démarches simplifiées'),
            ('Planification de voyage', 'Voyages organisés - Circuits personnalisés', 'fas fa-map-marked-alt', 'images/services/planning.jpg', 'Voyages organisés|Circuits personnalisés|Séjours thématiques'),
            ('Assurance voyage', 'Couverture complète et sécurisée', 'fas fa-shield-alt', 'images/services/insurance.jpg', "Annulation|Rapatriement|Santé à l'étranger|Bagages"),
        ]
        cursor.executemany('''
            INSERT INTO services (name, description, icon, image, features) 
            VALUES (?, ?, ?, ?, ?)
        ''', default_services)

    migrate_stock_photos(conn)
    migrate_english_columns(conn)
    conn.commit()
    conn.close()
    print("[SUCCES] Base de données initialisée avec succès")
    print(f"[SUCCES] Chemin utilisé : {DB_PATH}")


# Anciennes images "par défaut" (dont la photo de Marrakech filigranée « alamy »)
# remplacées par des photos libres de droits. Une image envoyée depuis l'admin
# n'est jamais remplacée.
OLD_DEFAULT_IMAGES = {
    '', 'images/destinations/default.jpg', 'images/destinations/paris.jpg', 'images/destinations/dubai.jpg',
    'images/destinations/marrakech.jpg', 'images/destinations/maldives.jpg', 'images/destinations/italy.jpg',
    'images/destinations/japan.jpg', 'images/destinations/newyork.jpg', 'images/destinations/london.jpg',
    'images/destinations/canada.jpg', 'images/destinations/switzerland.jpg', 'images/destinations/turkey.jpg',
    'images/destinations/greece.jpg', 'images/destinations/dakar.jpg', 'images/destinations/egypt.jpg',
    'images/destinations/bali.jpg', 'images/destinations/australia.jpg',
}
STOCK_PHOTOS = {
    'paris': 'paris', 'dubai': 'dubai', 'dubaï': 'dubai', 'marrakech': 'marrakech', 'maldives': 'maldives',
    'rome': 'rome', 'tokyo': 'tokyo', 'new york': 'new-york', 'londres': 'londres', 'london': 'londres',
    'montreal': 'montreal', 'montréal': 'montreal', 'zurich': 'zurich', 'istanbul': 'istanbul',
    'athenes': 'athenes', 'athènes': 'athenes', 'le caire': 'le-caire', 'bali': 'bali', 'sydney': 'sydney',
}


def migrate_stock_photos(conn):
    rows = conn.execute('SELECT id, name, image FROM destinations').fetchall()
    changed = 0
    for row in rows:
        photo = STOCK_PHOTOS.get((row['name'] or '').strip().lower())
        if photo and (row['image'] or '') in OLD_DEFAULT_IMAGES:
            conn.execute('UPDATE destinations SET image = ? WHERE id = ?',
                         (f'images/destinations/kta-{photo}.jpg', row['id']))
            changed += 1
    if changed:
        print(f"[MIGRATION] {changed} photo(s) de destination remplacée(s)")



# ---------------------------------------------------------------------------
# Version anglaise du contenu : colonnes *_en (vides = texte français affiché)
# ---------------------------------------------------------------------------
EN_COLUMNS = {
    'destinations': ['name_en', 'country_en', 'description_en'],
    'services': ['name_en', 'description_en', 'features_en'],
    'scholarship_opportunities': ['title_en', 'country_en', 'description_en', 'benefits_en', 'requirements_en'],
}

DEFAULT_DESTINATIONS_EN = {
    'paris': ('Paris', 'France', 'The city of light and love'),
    'dubai': ('Dubai', 'United Arab Emirates', 'Modern luxury and desert'),
    'marrakech': ('Marrakech', 'Morocco', 'The pearl of the South'),
    'maldives': ('Maldives', 'Maldives', 'Turquoise lagoons and overwater villas'),
    'rome': ('Rome', 'Italy', 'The Eternal City'),
    'tokyo': ('Tokyo', 'Japan', 'Where tradition meets modernity'),
    'new york': ('New York', 'United States', 'The city that never sleeps'),
    'londres': ('London', 'United Kingdom', 'The British capital'),
    'montreal': ('Montreal', 'Canada', 'Wide open spaces and wild nature'),
    'montréal': ('Montreal', 'Canada', 'Wide open spaces and wild nature'),
    'zurich': ('Zurich', 'Switzerland', 'Alps, chocolate and precision'),
    'istanbul': ('Istanbul', 'Türkiye', 'Where East meets West'),
    'athenes': ('Athens', 'Greece', 'Island paradise and ancient history'),
    'athènes': ('Athens', 'Greece', 'Island paradise and ancient history'),
    'dakar': ('Dakar', 'Senegal', 'The pearl of West Africa'),
    'le caire': ('Cairo', 'Egypt', 'The pyramids and an ancient civilisation'),
    'bali': ('Bali', 'Indonesia', 'Island of the gods, tropical paradise'),
    'sydney': ('Sydney', 'Australia', 'Opera House, beaches and kangaroos'),
}

DEFAULT_SERVICES_EN = {
    'billetterie aérienne': ('Flight tickets', 'Domestic and international flights at the best prices', 'Domestic and international flights|Competitive fares|Fast booking'),
    'billeterie aerienne': ('Flight tickets', 'Domestic and international flights at the best prices', 'Domestic and international flights|Competitive fares|Fast booking'),
    'réservation hôtelière': ('Hotel booking', 'Stays at home and abroad', 'Standard hotels|Superior comfort|Luxury and prestige'),
    'reservation hotels': ('Hotel booking', 'Stays at home and abroad', 'Standard hotels|Superior comfort|Luxury and prestige'),
    'assistance visa': ('Visa assistance', 'All types of visas, worldwide', 'Study|Tourism|Business|Full follow-up'),
    'pré-enrôlement': ('Passport & ID pre-enrolment', 'Passport and national ID card (CNI)', 'Passport|National ID card|Simplified paperwork'),
    'pre-enrolement': ('Passport & ID pre-enrolment', 'Passport and national ID card (CNI)', 'Passport|National ID card|Simplified paperwork'),
    'planification de voyage': ('Trip planning', 'Organised trips and tailor-made tours', 'Organised trips|Tailor-made tours|Themed stays'),
    'assurance voyage': ('Travel insurance', 'Complete, reliable cover', 'Cancellation|Repatriation|Healthcare abroad|Luggage'),
}


def migrate_english_columns(conn):
    for table, columns in EN_COLUMNS.items():
        existing = {row[1] for row in conn.execute(f'PRAGMA table_info({table})')}
        for column in columns:
            if column not in existing:
                conn.execute(f'ALTER TABLE {table} ADD COLUMN {column} TEXT')
    # Traductions des contenus livrés avec le site (jamais d'écrasement).
    for row in conn.execute('SELECT id, name, name_en FROM destinations').fetchall():
        en = DEFAULT_DESTINATIONS_EN.get((row['name'] or '').strip().lower())
        if en and not row['name_en']:
            conn.execute('UPDATE destinations SET name_en = ?, country_en = ?, description_en = ? WHERE id = ?',
                         (*en, row['id']))
    for row in conn.execute('SELECT id, name, name_en FROM services').fetchall():
        en = DEFAULT_SERVICES_EN.get((row['name'] or '').strip().lower())
        if en and not row['name_en']:
            conn.execute('UPDATE services SET name_en = ?, description_en = ?, features_en = ? WHERE id = ?',
                         (*en, row['id']))


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
    count = conn.execute("SELECT COUNT(*) FROM messages WHERE status = 'non lu'").fetchone()[0]
    conn.close()
    return count

def mark_message_as_read(message_id):
    conn = get_db()
    conn.execute("UPDATE messages SET status = 'lu' WHERE id = ?", (message_id,))
    conn.commit()
    conn.close()

def delete_message(message_id):
    conn = get_db()
    conn.execute('DELETE FROM messages WHERE id = ?', (message_id,))
    conn.commit()
    conn.close()

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
    try:
        flag_image = normalize_image_path(flag_image)
        image = normalize_image_path(image)
        conn = get_db()
        cursor = conn.execute('''
            INSERT INTO destinations (name, country, flag_image, description, price, image, continent)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, country, flag_image, description, price, image, continent))
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()
        return new_id
    except Exception as e:
        print(f"[ERREUR] add_destination: {e}")
        raise

def update_destination(destination_id, name, country, flag_image, description, price, image, continent):
    try:
        flag_image = normalize_image_path(flag_image)
        image = normalize_image_path(image)
        conn = get_db()
        conn.execute('''
            UPDATE destinations 
            SET name = ?, country = ?, flag_image = ?, description = ?, price = ?, image = ?, continent = ?
            WHERE id = ?
        ''', (name, country, flag_image, description, price, image, continent, destination_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[ERREUR] update_destination: {e}")
        raise

def delete_destination(destination_id):
    try:
        conn = get_db()
        conn.execute('DELETE FROM destinations WHERE id = ?', (destination_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[ERREUR] delete_destination: {e}")
        raise

def get_destinations_count():
    conn = get_db()
    count = conn.execute('SELECT COUNT(*) FROM destinations').fetchone()[0]
    conn.close()
    return count

def get_all_services():
    conn = get_db()
    services = conn.execute('SELECT * FROM services ORDER BY name').fetchall()
    conn.close()
    return services

def get_service_by_id(service_id):
    conn = get_db()
    service = conn.execute('SELECT * FROM services WHERE id = ?', (service_id,)).fetchone()
    conn.close()
    return service

def add_service(name, description, icon, image, features=''):
    image = normalize_image_path(image)
    conn = get_db()
    cursor = conn.execute('''
        INSERT INTO services (name, description, icon, image, features)
        VALUES (?, ?, ?, ?, ?)
    ''', (name, description, icon, image, features))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id

def update_service(service_id, name, description, icon, image, features):
    image = normalize_image_path(image)
    conn = get_db()
    conn.execute('''
        UPDATE services 
        SET name = ?, description = ?, icon = ?, image = ?, features = ?
        WHERE id = ?
    ''', (name, description, icon, image, features, service_id))
    conn.commit()
    conn.close()

def update_service_image(service_id, image):
    image = normalize_image_path(image)
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
    count = conn.execute("SELECT COUNT(*) FROM bookings WHERE status = 'en attente'").fetchone()[0]
    conn.close()
    return count

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
    count = conn.execute("SELECT COUNT(*) FROM scholarships WHERE status = 'en attente'").fetchone()[0]
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
        AND status = 'en attente'
    ''', (start_date, end_date)).fetchall()
    conn.close()
    return scholarships

def add_scholarship_opportunity(title, country, study_level, field_of_study,
                                start_date, end_date,
                                flag_url, image_url,
                                description, benefits, requirements):
    try:
        flag_url = normalize_image_path(flag_url)
        image_url = normalize_image_path(image_url)
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
    except Exception as e:
        print(f"[ERREUR] add_scholarship_opportunity: {e}")
        raise

def update_scholarship_opportunity(opportunity_id, title, country, study_level,
                                   field_of_study, start_date, end_date,
                                   flag_url, image_url,
                                   description, benefits, requirements):
    try:
        flag_url = normalize_image_path(flag_url)
        image_url = normalize_image_path(image_url)
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
        return True
    except Exception as e:
        print(f"[ERREUR] update_scholarship_opportunity: {e}")
        raise

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
    try:
        conn = get_db()
        conn.execute('DELETE FROM scholarship_opportunities WHERE id = ?', (opportunity_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[ERREUR] delete_scholarship_opportunity: {e}")
        raise

def migrate_image_paths():
    conn = get_db()
    cursor = conn.cursor()
    total_updated = 0

    for field in ['flag_image', 'image']:
        cursor.execute(f'''
            UPDATE destinations 
            SET {field} = 'images/' || {field} 
            WHERE {field} NOT LIKE 'http%' 
              AND {field} NOT LIKE 'images/%'
              AND {field} IS NOT NULL 
              AND {field} != ''
        ''')
        total_updated += cursor.rowcount

    cursor.execute('''
        UPDATE services 
        SET image = 'images/' || image 
        WHERE image NOT LIKE 'http%' 
          AND image NOT LIKE 'images/%'
          AND image IS NOT NULL 
          AND image != ''
    ''')
    total_updated += cursor.rowcount

    for field in ['flag_url', 'image_url']:
        cursor.execute(f'''
            UPDATE scholarship_opportunities 
            SET {field} = 'images/' || {field} 
            WHERE {field} NOT LIKE 'http%' 
              AND {field} NOT LIKE 'images/%'
              AND {field} IS NOT NULL 
              AND {field} != ''
        ''')
        total_updated += cursor.rowcount

    conn.commit()
    conn.close()
    print(f"[MIGRATION] {total_updated} chemins d'images corrigés.")
    return total_updated

def create_upload_folders():
    folders = [
        'static/images/flags',
        'static/images/destinations',
        'static/images/services',
        'static/images/scholarships'
    ]
    for folder in folders:
        try:
            os.makedirs(folder, exist_ok=True)
            os.chmod(folder, 0o777)
        except:
            pass

def save_translations(table, row_id, values):
    """Enregistre les champs anglais (*_en) d'une ligne. Seules les colonnes connues sont acceptées."""
    allowed = EN_COLUMNS.get(table, [])
    pairs = [(k, (v or '').strip()) for k, v in values.items() if k in allowed]
    if not row_id or not pairs:
        return
    conn = get_db()
    conn.execute(f"UPDATE {table} SET {', '.join(f'{k} = ?' for k, _ in pairs)} WHERE id = ?",
                 [v for _, v in pairs] + [row_id])
    conn.commit()
    conn.close()
