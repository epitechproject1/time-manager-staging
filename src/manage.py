#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv


def bootstrap_sqlite_and_admin() -> None:
    """
    DEV uniquement :
    - Charge le .env
    - Applique les migrations
    - Crée un superuser automatiquement (si absent)
    """

    # On ne bootstrap que pour runserver
    if len(sys.argv) < 2 or sys.argv[1] != "runserver":
        return

    # Évite la double exécution avec le reloader
    if os.environ.get("RUN_MAIN") != "true":
        return

    # Charger le .env depuis la racine du repo
    repo_root = Path(__file__).resolve().parent.parent
    load_dotenv(repo_root / ".env", override=False)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "primeBank.settings.dev")

    # Variables d'env pour le superuser
    username = os.getenv("DJANGO_SUPERUSER_USERNAME")
    password = os.getenv("DJANGO_SUPERUSER_PASSWORD")
    email = os.getenv("DJANGO_SUPERUSER_EMAIL", "")

    if not username or not password:
        print("⚠️ Superuser non créé (variables d'environnement manquantes)")
        return

    print("🔄 Vérification des migrations…")
    subprocess.run(
        [sys.executable, "manage.py", "migrate"],
        check=True,
    )

    print("👤 Vérification du superuser…")
    subprocess.run(
        [
            sys.executable,
            "manage.py",
            "createsuperuser",
            "--noinput",
            "--username",
            username,
            "--email",
            email,
        ],
        env={**os.environ, "DJANGO_SUPERUSER_PASSWORD": password},
        check=False,  # s'il existe déjà, Django renvoie une erreur → on ignore
    )


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "primeBank.settings.dev")

    bootstrap_sqlite_and_admin()

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
