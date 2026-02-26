from pathlib import Path

import environ
from dotenv import load_dotenv

# =============================================================================
# BASE
# =============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Charge le .env en local / docker-compose (env_file)
load_dotenv()
env = environ.Env()

# =============================================================================
# SECURITY
# =============================================================================

SECRET_KEY = env("SECRET_KEY", default=None)
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set")

DEBUG = env.bool("DEBUG", default=False)

AUTH_USER_MODEL = "users.User"

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

# =============================================================================
# APPLICATIONS
# =============================================================================

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # --- 3rd Party Apps ---
    "corsheaders",  # <--- [1] AJOUT OBLIGATOIRE ICI
    "rest_framework",
    "rest_framework.authtoken",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    # --- Local Apps ---
    "primeBank",
    "jwt_auth",
    "users",
    "contracts",
    "notifications",
    "permissions",
    "departments",
    "reset_password",
    "teams",
    "shift",
    "week_pattern",
    "time_slot_pattern",
    "assignment",
    "override",
    "clock_event",
    "clock_validation",
]

# =============================================================================
# MIDDLEWARE
# =============================================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# =============================================================================
# URLS / WSGI
# =============================================================================

ROOT_URLCONF = "primeBank.urls"
WSGI_APPLICATION = "primeBank.wsgi.application"

# =============================================================================
# TEMPLATES
# =============================================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# =============================================================================
# DATABASE
# =============================================================================

DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
    )
}

# =============================================================================
# I18N
# =============================================================================

LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Europe/Paris"

USE_I18N = True
USE_TZ = True

# =============================================================================
# STATIC FILES
# =============================================================================

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# =============================================================================
# PK
# =============================================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =============================================================================
# EMAIL (SMTP)
# =============================================================================

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

EXPIRY_MINUTES = env("EXPIRY_MINUTES", default=3)


EMAIL_HOST = env("EMAIL_HOST", default="smtp.sendgrid.net")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)

EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")

DEFAULT_FROM_EMAIL = env(
    "DEFAULT_FROM_EMAIL",
    default="PrimeBank <no-reply@primebank.com>",
)

# =============================================================================
# EXPORTS EXPLICITES
# =============================================================================

__all__ = [
    "BASE_DIR",
    "SECRET_KEY",
    "EMAIL_BACKEND",
    "EMAIL_HOST",
    "EMAIL_PORT",
    "EMAIL_USE_TLS",
    "EMAIL_HOST_USER",
    "EMAIL_HOST_PASSWORD",
    "EXPIRY_MINUTES",
    "DEBUG",
    "AUTH_USER_MODEL",
    "ALLOWED_HOSTS",
    "INSTALLED_APPS",
    "MIDDLEWARE",
    "ROOT_URLCONF",
    "WSGI_APPLICATION",
    "TEMPLATES",
    "DATABASES",
    "LANGUAGE_CODE",
    "TIME_ZONE",
    "USE_I18N",
    "USE_TZ",
    "STATIC_URL",
    "STATIC_ROOT",
    "DEFAULT_AUTO_FIELD",
]
