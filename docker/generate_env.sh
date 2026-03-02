#!/usr/bin/env bash
set -euo pipefail

ENV_FILE=".env"

# 1) Si déjà présent, on ne touche pas
if [ -f "$ENV_FILE" ]; then
  echo "✅ .env already exists"
  exit 0
fi

echo "ℹ️ .env not found, generating a default one..."

# 2) SECRET_KEY : openssl si dispo, sinon fallback
if command -v openssl >/dev/null 2>&1; then
  SECRET="$(openssl rand -hex 32)"
else
  SECRET="dev-secret-key-change-me"
fi

# 3) Génération .env (TES VALEURS)
cat > "$ENV_FILE" <<EOF
# Django
SECRET_KEY="$SECRET"
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

# Postgres (doit matcher docker-compose.yml)
POSTGRES_DB=timemanager
POSTGRES_USER=timemanager_user
POSTGRES_PASSWORD=timemanager_pass

# Utilisé par Django + Docker (IMPORTANT)
DATABASE_URL=postgresql://timemanager_user:timemanager_pass@db:5432/timemanager

# Admin Django
DJANGO_RESET_DB=true
DJANGO_ADMIN_EMAIL=admin@primebank.com
DJANGO_ADMIN_PASSWORD=Admin123!
DJANGO_ADMIN_FIRST_NAME=Prime
DJANGO_ADMIN_LAST_NAME=Admin

DISABLE_EMAILS=True

EXPIRY_MINUTES=5
SHIFT_RECORD_CODE_EXPIRY_MINUTES=5

CLOCK_IN_TOLERANCE_MINUTES=30
CLOCK_OUT_TOLERANCE_MINUTES=60

# Email (optionnel) - laisse vide par défaut
EMAIL_HOST="smtp.gmail.com"
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=""
EMAIL_HOST_PASSWORD=""

DEFAULT_FROM_EMAIL="PrimeBank <no-reply@primebank.local>"
EOF

echo "✅ .env generated"
echo "📌 You can edit it if needed."