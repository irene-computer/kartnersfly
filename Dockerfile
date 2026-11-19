FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data static/images/flags static/images/destinations \
    static/images/services static/images/scholarships

EXPOSE 8080

# Le port vient de la variable PORT (8080 sur Fly.io, voir fly.toml).
CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 1 --threads 8 --timeout 60 --access-logfile - app:app"]
