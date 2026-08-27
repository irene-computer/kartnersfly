# Dockerfile
# ============================================
# KARTNERSFLY - Configuration Docker
# ============================================

# Image de base Python
FROM python:3.10-slim

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py \
    FLASK_ENV=production \
    PORT=5000

# Créer le répertoire de travail
WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copier requirements.txt et installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier tout le code source
COPY . .

# Créer le dossier pour la base de données
RUN mkdir -p /app/instance

# Exposer le port
EXPOSE 5000

# Commande de démarrage
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
