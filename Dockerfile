# ============================================
# KARTNERSFLY - Dockerfile (Root)
# ============================================

FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py \
    FLASK_ENV=production \
    PORT=5000

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Créer le dossier instance et les dossiers d'upload
RUN mkdir -p instance static/images/flags static/images/destinations static/images/services static/images/scholarships

# Suppression de l'utilisateur non-root
# RUN adduser --disabled-password --gecos '' appuser && chown -R appuser:appuser /app
# USER appuser

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "3", "--threads", "2", "app:app"]