# ✈️ Kartners Travel Agency

**Voyagez comme vous l'imaginez** – Plateforme web professionnelle pour l'agence de voyage Kartners Travel Agency, basée à Douala, Cameroun.  
Découvrez nos destinations, réservez vos voyages, préparez vos visas et trouvez votre bourse d'études en toute simplicité.

---

## 🌐 Accès au site

| Accès | URL |
|-------|-----|
| **Site public** | [https://www.kartnersagency.com](https://www.kartnersagency.com) *(à venir)* |
| **Panel administration** | `/admin/login` |
| **API Contact** | `/api/contact` (POST) |
| **API Bourse** | `/api/scholarship` (POST) |
| **API Réservation** | `/api/booking` (POST) |
| **API Newsletter** | `/api/newsletter` (POST) |

---

## 📋 Fonctionnalités

### 👥 Frontend (Site public)

- **Destinations** : Parcours et recherche de destinations avec filtres (prix, pays).
- **Réservation en ligne** : Formulaire de réservation avec confirmation automatique par email.
- **Bourses d'études** : Présentation des opportunités de bourses avec modal de détails.
- **Formulaire de contact** : Envoi de messages avec notification par email.
- **Newsletter** : Inscription des utilisateurs à la newsletter.
- **Service Worker** : Mode hors-ligne et installation en tant qu'application PWA.
- **Design responsive** : Optimisé pour mobile, tablette et desktop.
- **Animations** : Effets de scroll, micro-interactions, transitions fluides.
- **Réseaux sociaux** : Liens vers WhatsApp, Instagram, Facebook, LinkedIn, TikTok, YouTube.

### 🛠️ Administration

- **Tableau de bord** : Statistiques globales (messages, réservations, destinations, services, bourses).
- **Gestion des messages** : Consultation, lecture et suppression des messages de contact.
- **Gestion des réservations** : Suivi, confirmation, annulation et export CSV.
- **Gestion des destinations** : CRUD complet (création, modification, suppression) avec upload d'images.
- **Gestion des services** : CRUD des services proposés (billeterie, visa, hôtel, etc.).
- **Gestion des bourses** : CRUD des opportunités de bourses avec upload d'images et gestion des périodes.
- **Newsletter** : Gestion des abonnés et envoi d'emails groupés.
- **Authentification** : Sécurisée avec session et protection IP.

### ⚙️ Techniques

- **Base de données** : SQLite avec migration automatique.
- **Upload d'images** : Stockage sécurisé avec noms uniques.
- **Emails transactionnels** : Envoi de confirmations et notifications.
- **Sécurité** : Sanitisation des entrées, protection CSRF, limitation des requêtes (`Flask-Limiter`), en-têtes de sécurité (`Talisman`).
- **Performances** : Lazy loading des images, cache des assets, optimisation CSS/JS.
- **SEO** : Meta tags, Open Graph, structure sémantique.

---

## 🛠️ Stack technique

### Backend

| Technologie | Version | Rôle |
|-------------|---------|------|
| **Python** | 3.10+ | Langage principal |
| **Flask** | 2.3.3 | Framework web |
| **SQLite** | 3.x | Base de données |
| **Gunicorn** | 21.x | Serveur WSGI (production) |
| **python-dotenv** | 1.x | Gestion des variables d'environnement |
| **Flask-Cors** | 4.0.1 | Gestion CORS |
| **Flask-Limiter** | 3.7.0 | Limitation de taux |
| **Flask-Talisman** | 1.1.0 | Sécurité HTTP |

### Frontend

| Technologie | Version | Rôle |
|-------------|---------|------|
| **Bootstrap** | 5.3.x | Framework CSS responsive |
| **Font Awesome** | 6.x | Bibliothèque d'icônes |
| **Inter** | Google Font | Typographie |
| **Flag-icons** | 7.2.x | Drapeaux des pays |
| **Vanilla JS** | ES6 | Interactions et dynamisme |

### Services externes

- **Gmail SMTP** : Envoi d'emails transactionnels.
- **Service Worker** : Fonctionnalités PWA.
- **flagcdn.com** : Drapeaux (fallback).

---

## 📁 Structure du projet
kartnersfly/
├── app.py # Point d'entrée principal
├── config.py # Configuration (variables, secrets)
├── models.py # Modèles et accès base de données
├── email_utils.py # Fonctions d'envoi d'emails
├── cron_job.py # Tâches planifiées (rappels, nettoyage)
├── check_db.py # Vérification/migration de la base
├── requirements.txt # Dépendances Python
├── Dockerfile # Conteneurisation
├── Procfile # Déploiement Heroku
├── database.db # Base SQLite (dev)
├── static/
│ ├── style.css # Styles principaux
│ ├── admin.css # Styles admin
│ ├── script.js # JavaScript commun
│ ├── sw.js # Service worker
│ ├── images/
│ │ ├── backgrounds/ # Images du slideshow
│ │ ├── destinations/ # Photos des destinations
│ │ ├── flags/ # Drapeaux des pays
│ │ ├── scholarships/ # Images des bourses
│ │ └── services/ # Icônes des services
│ └── manifest.json # Manifeste PWA
├── templates/
│ ├── base.html # Template de base
│ ├── index.html # Page d'accueil
│ ├── destinations.html # Destinations
│ ├── services.html # Services
│ ├── bourse_etudes.html # Bourses d'études
│ ├── about.html # À propos
│ ├── contact.html # Contact
│ ├── legal/ # Mentions légales, CGV, confidentialité
│ └── admin/ # Templates du back-office
│ ├── base_admin.html
│ ├── dashboard.html
│ ├── destinations_admin.html
│ ├── bookings.html
│ ├── scholarships.html
│ ├── scholarship_opportunities.html
│ ├── newsletter.html
│ ├── messages.html
│ └── login.html
└── tests/ # Tests unitaires (non inclus)

---

## 🚀 Installation et déploiement

### Prérequis

- Python 3.10 ou supérieur
- Git
- (Optionnel) Serveur SMTP pour les emails

### Étapes d'installation

1. **Cloner le dépôt**
```bash
git clone https://github.com/votre-compte/kartnersfly.git
cd kartnersfly

---

## 🔐 Variables d'environnement

| Variable | Obligatoire | Rôle |
|----------|-------------|------|
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | Oui | Identifiants du panneau `/admin`. Sans eux, la connexion admin est désactivée. |
| `ADMIN_PASSWORD_HASH` | Recommandé | Empreinte du mot de passe, à la place de `ADMIN_PASSWORD` (`python manage_security.py hash` ou page Admin › Sécurité). |
| `ADMIN_TOTP_SECRET` | Recommandé | Active la double authentification (`python manage_security.py totp` ou page Admin › Sécurité). |
| `AUTO_BACKUP` / `BACKUP_DIR` | Non | Sauvegarde quotidienne de la base (activée par défaut, 14 copies dans `backups/` à côté de la base). |
| `NOTIFY_EMAIL` | Non | Adresse qui reçoit une alerte à chaque réservation, message ou candidature (par défaut : l'email de contact). |
| `CALLMEBOT_PHONE` / `CALLMEBOT_APIKEY` | Non | Alerte WhatsApp gratuite via CallMeBot (voir `notify.py` pour l'activation). |
| `SECRET_KEY` | Recommandé | Clé de session. Si absente, une clé est générée une fois et conservée dans `.secret_key` à côté de la base. |
| `DATABASE` | Non | Chemin de la base SQLite (`/data/database.db` sur Fly.io). |
| `UPLOAD_ROOT` | Non | Dossier persistant des images envoyées depuis l'admin (`/data/uploads` sur Fly.io), pour qu'elles survivent aux déploiements. |
| `MAIL_USERNAME` / `MAIL_PASSWORD` | Pour les emails | Compte SMTP (mot de passe d'application Gmail). |
| `SESSION_COOKIE_SECURE` | Non | `True` par défaut sur Fly.io, `False` en local (http). |
| `DEBUG` | Non | `True` uniquement en développement. |

Sur Fly.io : `fly secrets set ADMIN_USERNAME=... ADMIN_PASSWORD=... SECRET_KEY=...`

### Lancer en local

```bash
pip install -r requirements.txt
ADMIN_USERNAME=admin ADMIN_PASSWORD=motdepasse DEBUG=True python app.py
```

## 🛡️ Sécurité

- Requêtes SQL paramétrées partout (pas d'injection SQL).
- En-têtes `Content-Security-Policy` (scripts limités au site et aux blocs signés par un nonce), HSTS, `X-Frame-Options`, `nosniff`.
- Connexion admin : blocage après 5 échecs en 15 min par adresse IP (et 30 par heure au total), conservé en base ; double authentification TOTP en option ; sessions révoquées quand le mot de passe change.
- Formulaires publics : champ piège anti-robots, jeton signé, délai minimum de saisie, 10 envois par heure et par adresse IP.
- Page **Admin › Sécurité & sauvegardes** : journal des connexions, recherche de contenus suspects en base, sauvegardes téléchargeables.

## 🌍 Langues, thème, prix

- **Bilingue français / anglais** : bouton FR / EN dans l'en-tête (`?lang=en`, mémorisé). Textes de l'interface dans `i18n.py` ; contenus (destinations, services, bourses) traduits depuis l'admin, champs « Version anglaise ».
- **Thème clair / sombre** : suit le réglage de l'appareil, bouton lune / soleil pour forcer un thème.
- **Prix en FCFA** : saisis en euros dans l'admin, affichés en francs CFA (parité fixe 1 € = 655,957 FCFA) avec l'équivalent en euros.
- **Photos des destinations** : Unsplash, licence libre (voir `static/images/destinations/CREDITS.md`).
