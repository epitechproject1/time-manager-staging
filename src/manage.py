#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv


def bootstrap_sqlite_and_admin() -> None:
    """
    DEV uniquement :
    - Charge le .env
    - Applique les migrations
    - Crée un utilisateur ADMIN dans la table User (si absent)
    """

    # Seulement pour runserver
    if len(sys.argv) < 2 or sys.argv[1] != "runserver":
        return

    # Éviter double exécution avec le reloader
    if os.environ.get("RUN_MAIN") != "true":
        return

    # Charger le .env
    repo_root = Path(__file__).resolve().parent.parent
    load_dotenv(repo_root / ".env", override=False)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "primeBank.settings.dev")

    email = os.getenv("DJANGO_ADMIN_EMAIL")
    password = os.getenv("DJANGO_ADMIN_PASSWORD")
    first_name = os.getenv("DJANGO_ADMIN_FIRST_NAME", "Admin")
    last_name = os.getenv("DJANGO_ADMIN_LAST_NAME", "User")

    if not email or not password:
        print("⚠️ Admin non créé (variables manquantes)")
        return

    import django

    django.setup()

    from django.core.management import call_command

    from users.constants import UserRole
    from users.models import User

    print("🔄 Vérification des migrations…")
    call_command("migrate", interactive=False)

    print("👤 Vérification de l'utilisateur ADMIN…")

    if User.objects.filter(email=email).exists():
        print("✅ Admin déjà existant")
        return

    User.objects.create_superuser(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        role=UserRole.ADMIN,
    )

def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "primeBank.settings.dev")

    bootstrap_sqlite_and_admin()

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
