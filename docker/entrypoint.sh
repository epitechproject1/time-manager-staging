#!/bin/sh
set -e

echo "⏳ Waiting for database..."

python - <<'EOF'
import os
import time
from urllib.parse import urlparse

import psycopg

url = os.environ.get("DATABASE_URL")
if not url:
    raise SystemExit("DATABASE_URL is not set")

u = urlparse(url)

host = u.hostname
port = u.port or 5432
user = u.username
password = u.password
dbname = u.path.lstrip("/")

for i in range(30):
    try:
        conn = psycopg.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            dbname=dbname,
        )
        conn.close()
        print("✅ Database is ready")
        break
    except Exception:
        print("⏳ Database not ready, retrying...")
        time.sleep(1)
else:
    raise SystemExit("❌ Database not ready after 30 seconds")
EOF

echo "📦 Applying database migrations..."
python manage.py migrate --noinput

echo "🎨 Collecting static files..."
python manage.py collectstatic --noinput

# Optionnel: création automatique d'un admin (utile en staging / projet académique)
if [ -n "$DJANGO_ADMIN_EMAIL" ] && [ -n "$DJANGO_ADMIN_PASSWORD" ]; then
  echo "👤 Creating admin user if not exists..."

  python manage.py shell - <<'EOF'
from django.contrib.auth import get_user_model
import os

User = get_user_model()

email = os.environ.get("DJANGO_ADMIN_EMAIL")
password = os.environ.get("DJANGO_ADMIN_PASSWORD")
first = os.environ.get("DJANGO_ADMIN_FIRST_NAME", "Admin")
last = os.environ.get("DJANGO_ADMIN_LAST_NAME", "User")

# ⚠️ Ici on suppose que ton User utilise "email" comme identifiant.
# Si ce n'est pas le cas, dis-moi et je l'adapte.
if email and password and not User.objects.filter(email=email).exists():
    User.objects.create_superuser(
        email=email,
        password=password,
        first_name=first,
        last_name=last,
    )
    print("✅ Admin user created")
else:
    print("ℹ️ Admin already exists or missing env vars")
EOF
fi

echo "🚀 Starting server..."
exec "$@"
