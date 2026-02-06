#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv


def bootstrap_dev_and_admin() -> None:
    """
    DEV uniquement :
    - Charge le .env
    - Applique les migrations
    - Crée un superuser automatiquement (si absent)
    """

    # On ne bootstrap que pour runserver
    if len(sys.argv) < 2 or sys.argv[1] != "runserver":
        return

    # Évite la double exécution avec le reloader Django (une seule fois)
    if os.environ.get("RUN_MAIN") != "true":
        return

    # Charger le .env depuis la racine du repo
    repo_root = Path(__file__).resolve().parent.parent
    load_dotenv(repo_root / ".env", override=False)

    # S'assurer que le settings module est défini avant tout import Django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "primeBank.settings.dev")

    username = os.getenv("DJANGO_SUPERUSER_USERNAME")
    password = os.getenv("DJANGO_SUPERUSER_PASSWORD")
    email = os.getenv("DJANGO_SUPERUSER_EMAIL", "")

    if not username or not password:
        print("⚠️ Superuser non créé (variables d'environnement manquantes)")
        return

    # Initialiser Django avant d'utiliser call_command
    # ORM (corrige AppRegistryNotReady)
    import django

    django.setup()

    from django.contrib.auth import get_user_model
    from django.core.management import call_command

    print("🔄 Vérification des migrations…")
    call_command("migrate", interactive=False)

    print("👤 Vérification du superuser…")
    User = get_user_model()

    # Si ton projet utilise email comme identifiant, adapte le filtre (email=email)
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username=username, email=email, password=password)
        print("✅ Superuser créé.")
    else:
        print("ℹ️ Superuser existe déjà.")


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "primeBank.settings.dev")

    bootstrap_dev_and_admin()

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
