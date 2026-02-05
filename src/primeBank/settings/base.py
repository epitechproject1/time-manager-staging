import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set")

DEBUG = False

ALLOWED_HOSTS = os.getenv(
    "ALLOWED_HOSTS",
    "localhost,127.0.0.1",
).split(",")

INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "rest_framework.authtoken",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "primeBank.urls"
WSGI_APPLICATION = "primeBank.wsgi.application"

LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Europe/Paris"

USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# 🔐 Exports explicites (important pour flake8 & lisibilité)
__all__ = [
    "BASE_DIR",
    "SECRET_KEY",
    "DEBUG",
    "ALLOWED_HOSTS",
    "INSTALLED_APPS",
    "MIDDLEWARE",
    "ROOT_URLCONF",
    "WSGI_APPLICATION",
    "LANGUAGE_CODE",
    "TIME_ZONE",
    "USE_I18N",
    "USE_TZ",
    "STATIC_URL",
    "STATIC_ROOT",
    "DEFAULT_AUTO_FIELD",
]
