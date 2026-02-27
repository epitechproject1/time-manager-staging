#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv


def reset_database() -> None:
    """Supprime et recrée la base de données"""
    repo_root = Path(__file__).resolve().parent.parent
    db_path = repo_root / "users" / "db.sqlite3"

    if db_path.exists():
        print(f"🗑️  Suppression de la base de données existante : {db_path}")
        db_path.unlink()
        print("✅ Base de données supprimée")

    print("🔄 Création des migrations...")
    from django.core.management import call_command

    call_command("makemigrations", interactive=False)

    print("🔄 Application des migrations...")
    call_command("migrate", interactive=False)


def list_all_tables() -> None:
    """Liste toutes les tables et leur contenu"""
    from django.db import connection

    print("\n📋 Tables créées dans la base de données :")
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
        )
        tables = cursor.fetchall()

        if not tables:
            print("  Aucune table trouvée")
            return

        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                count = cursor.fetchone()[0]
                print(f"  - {table[0]}: {count} enregistrement(s)")
            except Exception:
                print(f"  - {table[0]}")


def create_admin_if_not_exists() -> None:
    """Crée l'admin si nécessaire"""
    repo_root = Path(__file__).resolve().parent.parent
    load_dotenv(repo_root / ".env", override=False)

    email = os.getenv("DJANGO_ADMIN_EMAIL")
    password = os.getenv("DJANGO_ADMIN_PASSWORD")
    first_name = os.getenv("DJANGO_ADMIN_FIRST_NAME", "Admin")
    last_name = os.getenv("DJANGO_ADMIN_LAST_NAME", "User")

    if not email or not password:
        print("⚠️ Admin non créé (variables manquantes)")
        return

    from users.constants import UserRole
    from users.models import User

    print("👤 Vérification de l'utilisateur ADMIN…")
    if not User.objects.filter(email=email).exists():
        User.objects.create_superuser(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=UserRole.ADMIN,
        )
        print("✅ Admin créé")


def bootstrap_sqlite_and_admin() -> None:
    """DEV uniquement : comportement au lancement de runserver"""

    if len(sys.argv) < 2 or sys.argv[1] != "runserver":
        return

    if os.environ.get("RUN_MAIN") != "true":
        return

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "primeBank.settings.dev")

    import django

    django.setup()

    # 🔥 Vérifier si on doit reset la DB
    reset = os.getenv("DJANGO_RESET_DB", "false").lower() == "true"

    if reset:
        reset_database()
    else:
        print("🔄 Vérification des migrations…")
        from django.core.management import call_command

        call_command("migrate", interactive=False)

    # 📋 Lister les tables
    list_all_tables()

    # 👤 Créer l'admin
    create_admin_if_not_exists()

    # 📊 Statistiques finales
    from users.models import User

    print("\n📊 Statistiques finales :")
    print(f"  - Utilisateurs: {User.objects.count()}")
    print(f"  - Superusers: {User.objects.filter(is_superuser=True).count()}")


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "primeBank.settings.dev")

    # Commandes personnalisées
    if len(sys.argv) > 1:
        if sys.argv[1] == "reset_db":
            os.environ.setdefault("DJANGO_SETTINGS_MODULE", "primeBank.settings.dev")
            import django

            django.setup()
            reset_database()
            list_all_tables()
            create_admin_if_not_exists()
            return

        elif sys.argv[1] == "list_tables":
            os.environ.setdefault("DJANGO_SETTINGS_MODULE", "primeBank.settings.dev")
            import django

            django.setup()
            list_all_tables()
            return

    bootstrap_sqlite_and_admin()

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
