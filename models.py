import sqlite3
from datetime import datetime
from config import Config
import os

# Chemin vers votre base de donnees
DB_PATH = Config.DATABASE if hasattr(Config, 'DATABASE') else 'database.db'

def get_db():
    """Retourne une connexion a la base de donnees"""
    os.makedirs(os.path.dirname(DB_PATH) if os.path.dirname(DB_PATH) else '.', exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialise toutes les tables de la base de donnees"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Table des messages de contact - AJOUT de la colonne service
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
    
    # Table des destinations
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
    
    # Table des services
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
    
    # Table des reservations (bookings)
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
    
    # Table newsletter
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS newsletter (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insertion des destinations par defaut
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
    
    # Insertion des services par defaut
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
    print("Base de donnees initialisee avec succes")


# ==================== FONCTIONS POUR LES MESSAGES ====================

def add_message(name, email, phone, service, message):
    """Ajoute un nouveau message de contact avec le service concerne"""
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
    """Recupere tous les messages classes par date decroissante"""
    conn = get_db()
    messages = conn.execute('SELECT * FROM messages ORDER BY created_at DESC').fetchall()
    conn.close()
    return messages


def get_unread_messages_count():
    """Recupere le nombre de messages non lus"""
    conn = get_db()
    count = conn.execute('SELECT COUNT(*) FROM messages WHERE status = "non lu"').fetchone()[0]
    conn.close()
    return count


def mark_message_as_read(message_id):
    """Marque un message comme lu"""
    conn = get_db()
    conn.execute('UPDATE messages SET status = "lu" WHERE id = ?', (message_id,))
    conn.commit()
    conn.close()


def delete_message(message_id):
    """Supprime un message"""
    conn = get_db()
    conn.execute('DELETE FROM messages WHERE id = ?', (message_id,))
    conn.commit()
    conn.close()


# ==================== FONCTIONS POUR LES DESTINATIONS ====================

def get_all_destinations():
    """Recupere toutes les destinations"""
    conn = get_db()
    destinations = conn.execute('SELECT * FROM destinations ORDER BY name').fetchall()
    conn.close()
    return destinations


def get_destination_by_id(destination_id):
    """Recupere une destination par son ID"""
    conn = get_db()
    destination = conn.execute('SELECT * FROM destinations WHERE id = ?', (destination_id,)).fetchone()
    conn.close()
    return destination


def add_destination(name, country, flag_image, description, price, image, continent='europe'):
    """Ajoute une nouvelle destination"""
    conn = get_db()
    conn.execute('''
        INSERT INTO destinations (name, country, flag_image, description, price, image, continent)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (name, country, flag_image, description, price, image, continent))
    conn.commit()
    conn.close()


def update_destination(destination_id, name, country, flag_image, description, price, image, continent):
    """Met a jour une destination"""
    conn = get_db()
    conn.execute('''
        UPDATE destinations 
        SET name = ?, country = ?, flag_image = ?, description = ?, price = ?, image = ?, continent = ?
        WHERE id = ?
    ''', (name, country, flag_image, description, price, image, continent, destination_id))
    conn.commit()
    conn.close()


def delete_destination(destination_id):
    """Supprime une destination"""
    conn = get_db()
    conn.execute('DELETE FROM destinations WHERE id = ?', (destination_id,))
    conn.commit()
    conn.close()


def get_destinations_count():
    """Recupere le nombre de destinations"""
    conn = get_db()
    count = conn.execute('SELECT COUNT(*) FROM destinations').fetchone()[0]
    conn.close()
    return count


# ==================== FONCTIONS POUR LES SERVICES ====================

def get_all_services():
    """Recupere tous les services"""
    conn = get_db()
    services = conn.execute('SELECT * FROM services ORDER BY name').fetchall()
    conn.close()
    return services


def add_service(name, description, icon, image, features=''):
    """Ajoute un nouveau service"""
    conn = get_db()
    conn.execute('''
        INSERT INTO services (name, description, icon, image, features)
        VALUES (?, ?, ?, ?, ?)
    ''', (name, description, icon, image, features))
    conn.commit()
    conn.close()


def update_service(service_id, name, description, icon, features):
    """Met a jour un service"""
    conn = get_db()
    conn.execute('''
        UPDATE services 
        SET name = ?, description = ?, icon = ?, features = ?
        WHERE id = ?
    ''', (name, description, icon, features, service_id))
    conn.commit()
    conn.close()


def update_service_image(service_id, image):
    """Met a jour l'image d'un service"""
    conn = get_db()
    conn.execute('UPDATE services SET image = ? WHERE id = ?', (image, service_id))
    conn.commit()
    conn.close()


def delete_service(service_id):
    """Supprime un service"""
    conn = get_db()
    conn.execute('DELETE FROM services WHERE id = ?', (service_id,))
    conn.commit()
    conn.close()


def get_services_count():
    """Recupere le nombre de services"""
    conn = get_db()
    count = conn.execute('SELECT COUNT(*) FROM services').fetchone()[0]
    conn.close()
    return count


# ==================== FONCTIONS POUR LES RESERVATIONS ====================

def add_booking(destination_id, destination_name, fullname, email, phone, departure_date, travelers, message):
    """Ajoute une nouvelle reservation"""
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
    """Recupere toutes les reservations"""
    conn = get_db()
    bookings = conn.execute('''
        SELECT b.*, d.name as dest_name 
        FROM bookings b 
        LEFT JOIN destinations d ON b.destination_id = d.id 
        ORDER BY b.created_at DESC
    ''').fetchall()
    conn.close()
    return bookings


def update_booking_status(booking_id, status):
    """Met a jour le statut d'une reservation"""
    conn = get_db()
    conn.execute('UPDATE bookings SET status = ? WHERE id = ?', (status, booking_id))
    conn.commit()
    conn.close()


def delete_booking(booking_id):
    """Supprime une reservation"""
    conn = get_db()
    conn.execute('DELETE FROM bookings WHERE id = ?', (booking_id,))
    conn.commit()
    conn.close()


def get_pending_bookings_count():
    """Recupere le nombre de reservations en attente"""
    conn = get_db()
    count = conn.execute('SELECT COUNT(*) FROM bookings WHERE status = "en attente"').fetchone()[0]
    conn.close()
    return count


# ==================== FONCTIONS POUR LA NEWSLETTER ====================

def subscribe_newsletter(email):
    """Ajoute un email a la newsletter"""
    conn = get_db()
    conn.execute('INSERT OR IGNORE INTO newsletter (email) VALUES (?)', (email,))
    conn.commit()
    conn.close()


def get_newsletter_count():
    """Recupere le nombre d'abonnes a la newsletter"""
    conn = get_db()
    count = conn.execute('SELECT COUNT(*) FROM newsletter').fetchone()[0]
    conn.close()
    return count


# ==================== INITIALISATION ====================

# Creer les dossiers d'images s'ils n'existent pas
def create_upload_folders():
    folders = [
        'static/images/flags',
        'static/images/destinations',
        'static/images/services'
    ]
    for folder in folders:
        os.makedirs(folder, exist_ok=True)