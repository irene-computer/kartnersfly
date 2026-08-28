import sqlite3
from datetime import datetime, timedelta
from config import Config
import os
import re
from werkzeug.utils import secure_filename

DB_PATH = Config.DATABASE

def get_db():
    global DB_PATH
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        try:
            os.makedirs(db_dir, exist_ok=True, mode=0o777)
            test_file = os.path.join(db_dir, '.write_test')
            with open(test_file, 'w') as f:
                f.write('ok')
            os.remove(test_file)
            print(f"[INFO] Dossier {db_dir} accessible en écriture.")
        except Exception as e:
            print(f"[ERREUR] Dossier {db_dir} non accessible : {e}")
            fallback_dir = '/tmp'
            DB_PATH = os.path.join(fallback_dir, 'database.db')
            os.makedirs(fallback_dir, exist_ok=True)
            print(f"[INFO] Fallback vers {DB_PATH}")

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        print(f"[INFO] Connexion réussie à {DB_PATH}")
        return conn
    except sqlite3.OperationalError as e:
        print(f"[ERREUR] Connexion échouée à {DB_PATH} : {e}")
        fallback_path = 'database.db'
        print(f"[INFO] Fallback vers {fallback_path}")
        conn = sqlite3.connect(fallback_path)
        conn.row_factory = sqlite3.Row
        DB_PATH = fallback_path
        print(f"[INFO] Connexion réussie à {fallback_path}")
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
        default_destinations = [
            ('Paris', 'France', 'images/flags/france.png', 'La ville des lumieres et de l\'amour', 850, 'images/destinations/paris.jpg', 'europe'),
            ('Dubai', 'Emirats Arabes Unis', 'images/flags/uae.png', 'Luxe moderne et desert', 1200, 'images/destinations/dubai.jpg', 'asie'),
            ('Marrakech', 'Maroc', 'images/flags/morocco.png', 'La perle du Sud', 650, 'images/destinations/marrakech.jpg', 'afrique'),
            ('Maldives', 'Maldives', 'images/flags/maldives.png', 'Lagons turquoise et villas sur l\'eau', 2890, 'images/destinations/maldives.jpg', 'asie'),
            ('Rome', 'Italie', 'images/flags/italy.png', 'La ville eternelle', 1590, 'images/destinations/italy.jpg', 'europe'),
            ('Tokyo', 'Japon', 'images/flags/japan.png', 'Entre tradition et modernite', 3250, 'images/destinations/japan.jpg', 'asie'),
            ('New York', 'Etats-Unis', 'images/flags/usa.png', 'La ville qui ne dort jamais', 1990, 'images/destinations/newyork.jpg', 'amerique'),
            ('Londres', 'Royaume-Uni', 'images/flags/uk.png', 'La capitale britannique', 1450, 'images/destinations/london.jpg', 'europe'),
            ('Montreal', 'Canada', 'images/flags/canada.png', 'Grands espaces et nature sauvage', 2450, 'images/destinations/canada.jpg', 'amerique'),
            ('Zurich', 'Suisse', 'images/flags/switzerland.png', 'Alpes, chocolat et precision', 2200, 'images/destinations/switzerland.jpg', 'europe'),
            ('Istanbul', 'Turquie', 'images/flags/turkey.png', 'Ou l\'Orient rencontre l\'Occident', 1490, 'images/destinations/turkey.jpg', 'asie'),
            ('Athenes', 'Grece', 'images/flags/greece.png', 'Iles paradisiaques et histoire', 1690, 'images/destinations/greece.jpg', 'europe'),
            ('Dakar', 'Senegal', 'images/flags/senegal.png', 'La perle de l\'Afrique de l\'Ouest', 890, 'images/destinations/dakar.jpg', 'afrique'),
            ('Le Caire', 'Egypte', 'images/flags/egypt.png', 'Les pyramides et la civilisation antique', 1350, 'images/destinations/egypt.jpg', 'afrique'),
            ('Bali', 'Indonesie', 'images/flags/indonesia.png', 'Ile des dieux et paradis tropical', 1850, 'images/destinations/bali.jpg', 'asie'),
            ('Sydney', 'Australie', 'images/flags/australia.png', 'Opera, plages et kangourous', 3200, 'images/destinations/australia.jpg', 'oceanie'),
        ]
        cursor.executemany('''
            INSERT INTO destinations (name, country, flag_image, description, price, image, continent) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', default_destinations)

    cursor.execute("SELECT COUNT(*) FROM services")
    if cursor.fetchone()[0] == 0:
        default_services = [
            ('Billeterie aerienne', 'Vols nationaux et internationaux aux meilleurs prix', 'fas fa-plane-departure', 'images/services/airline.jpg', 'Vols nationaux|Tarifs competitis|Reservation rapide'),
            ('Reservation hotels', 'Sejours nationaux et internationaux', 'fas fa-hotel', 'images/services/hotel.jpg', 'Hotels standards|Confort superieur|Luxe et prestige'),
            ('Assistance visa', 'Tous types de visas pour le monde entier', 'fas fa-passport', 'images/services/visa.jpg', 'Etudes|Tourisme|Affaires|Suivi complet'),
            ('Pre-enrolement', 'Passeport - Carte Nationale d\'Identite (CNI)', 'fas fa-id-card', 'images/services/passport.jpg', 'Passeport|CNI|Demarches simplifiees'),
            ('Planification de voyage', 'Voyages organises - Circuits personnalises', 'fas fa-map-marked-alt', 'images/services/planning.jpg', 'Voyages organises|Circuits personnalises|Sejours thematiques'),
            ('Assurance voyage', 'Couverture complete et securisee', 'fas fa-shield-alt', 'images/services/insurance.jpg', 'Annulation|Rapatriement|Sante a l\'etranger|Bagages'),
        ]
        cursor.executemany('''
            INSERT INTO services (name, description, icon, image, features) 
            VALUES (?, ?, ?, ?, ?)
        ''', default_services)

    conn.commit()
    conn.close()
    print("[SUCCES] Base de données initialisée avec succès")
    print(f"[SUCCES] Chemin utilisé : {DB_PATH}")

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
        conn.execute('''
            INSERT INTO destinations (name, country, flag_image, description, price, image, continent)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, country, flag_image, description, price, image, continent))
        conn.commit()
        conn.close()
        return True
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
    conn.execute('''
        INSERT INTO services (name, description, icon, image, features)
        VALUES (?, ?, ?, ?, ?)
    ''', (name, description, icon, image, features))
    conn.commit()
    conn.close()

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
    count = conn.execute('SELECT COUNT(*) FROM bookings WHERE status = "en attente"').fetchone()[0]
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