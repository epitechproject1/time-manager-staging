#!/usr/bin/env python
import os
import sys
from pathlib import Path

from dotenv import load_dotenv


def bootstrap_sqlite_and_admin():
    """
    - Charge le .env
    - Applique les migrations
    - Crée un superuser si absent
    (DEV uniquement)
    """

    # 📦 Charger le .env explicitement
    BASE_DIR = Path(__file__).resolve().parent
    load_dotenv(BASE_DIR / ".env")

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "primeBank.settings.dev")

    try:
        import django

        django.setup()

        from django.conf import settings
        from django.contrib.auth import get_user_model
        from django.core.management import call_command

        # Sécurité : uniquement SQLite
        db = settings.DATABASES["default"]
        if db["ENGINE"] != "django.db.backends.sqlite3":
            return

        # 1️⃣ Appliquer les migrations manquantes
        print("🔄 Vérification des migrations…")
        call_command("migrate", interactive=False, verbosity=0)

        # 2️⃣ Récupérer les variables sensibles depuis l'env
        username = os.getenv("DJANGO_SUPERUSER_USERNAME")
        email = os.getenv("DJANGO_SUPERUSER_EMAIL")
        password = os.getenv("DJANGO_SUPERUSER_PASSWORD")

        if not all([username, email, password]):
            print("⚠️ Superuser non créé (variables d'environnement manquantes)")
            return

        # 3️⃣ Créer le superuser s'il n'existe pas
        User = get_user_model()

        if not User.objects.filter(username=username).exists():
            print(f"👤 Création du superuser {username}")
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
            )
        else:
            print(f"👤 Superuser déjà existant : {username}")

    except Exception as e:
        print("❌ Erreur bootstrap Django :", e)


def main():
    bootstrap_sqlite_and_admin()

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
