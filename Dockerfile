FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Dépendances système pour PostgreSQL (psycopg/psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Installer dépendances Python
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r /app/requirements.txt

# Copier le code
COPY . /app

# Fix CRLF + rendre exécutable
RUN sed -i 's/\r$//' /app/docker/entrypoint.sh \
 && chmod +x /app/docker/entrypoint.sh

# Ton projet Django est dans src/
WORKDIR /app/src

EXPOSE 8000

# IMPORTANT: laisser l'entrypoint gérer migrate/collectstatic/seed, puis lancer gunicorn
ENTRYPOINT ["/app/docker/entrypoint.sh"]
CMD ["gunicorn", "primeBank.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]