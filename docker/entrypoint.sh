#!/bin/sh
set -e

cd /app/src

echo "⏳ Waiting for database..."

python - <<'PY'
import os, time
from urllib.parse import urlparse

url = os.environ.get("DATABASE_URL")
if not url:
    raise SystemExit("❌ DATABASE_URL is not set")

try:
    import psycopg
except Exception as e:
    raise SystemExit("❌ psycopg not installed. Add 'psycopg' to requirements.txt") from e

u = urlparse(url)
host = u.hostname
port = u.port or 5432
user = u.username
password = u.password
dbname = u.path.lstrip("/")

for i in range(60):
    try:
        conn = psycopg.connect(host=host, port=port, user=user, password=password, dbname=dbname)
        conn.close()
        print("✅ Database ready")
        break
    except Exception:
        print(f"⏳ DB not ready (attempt {i+1}/60)...")
        time.sleep(1)
else:
    raise SystemExit("❌ DB not ready after 60 seconds")
PY

echo "📦 Applying migrations..."
python manage.py migrate --noinput

echo "🎨 Collecting static files..."
python manage.py collectstatic --noinput

# -------------------------
# Fixtures (OPTIONNEL)
# -------------------------
if [ "${LOAD_FIXTURES:-false}" = "true" ] && [ -f "/app/docker/fixtures/initial_data.json" ]; then
  echo "🌱 Loading fixtures..."
  if python manage.py loaddata /app/docker/fixtures/initial_data.json; then
    echo "✅ Fixtures loaded"
  else
    echo "⚠️ Fixtures failed to load (ignored for demo stability)"
  fi
else
  echo "ℹ️ Fixtures disabled (set LOAD_FIXTURES=true to enable)"
fi

# -------------------------
# Admin creation (via manage.py only)
# -------------------------
echo "👤 Ensure admin user exists (from .env)..."

export DJANGO_SUPERUSER_EMAIL="${DJANGO_ADMIN_EMAIL}"
export DJANGO_SUPERUSER_PASSWORD="${DJANGO_ADMIN_PASSWORD}"
export DJANGO_SUPERUSER_FIRST_NAME="${DJANGO_ADMIN_FIRST_NAME}"
export DJANGO_SUPERUSER_LAST_NAME="${DJANGO_ADMIN_LAST_NAME}"

# crée seulement si l'utilisateur n'existe pas déjà
python manage.py shell -c "from django.contrib.auth import get_user_model; U=get_user_model(); import os; email=os.getenv('DJANGO_SUPERUSER_EMAIL'); pwd=os.getenv('DJANGO_SUPERUSER_PASSWORD'); fn=os.getenv('DJANGO_SUPERUSER_FIRST_NAME',''); ln=os.getenv('DJANGO_SUPERUSER_LAST_NAME',''); 
u=U.objects.filter(email=email).first(); 
print('✅ Admin already exists' if u else '✅ Creating admin...'); 
(0 if u else U.objects.create_superuser(email=email, password=pwd, first_name=fn, last_name=ln))" || true

echo "🚀 Starting server..."
exec "$@"