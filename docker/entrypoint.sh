#!/bin/sh
set -e

echo "Waiting for database..."

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

for _ in range(60):
    try:
        conn = psycopg.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            dbname=dbname,
        )
        conn.close()
        print("Database is ready")
        break
    except Exception:
        print("Database not ready, retrying...")
        time.sleep(1)
else:
    raise SystemExit("Database not ready after 60 seconds")
EOF

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting server..."
exec "$@"
