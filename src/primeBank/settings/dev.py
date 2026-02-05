from . import base

# =============================================================================
# ENV DEV
# =============================================================================

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# =============================================================================
# TEMPLATES
# =============================================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [base.BASE_DIR / "templates"],
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
# DATABASE (SQLite DEV)
# =============================================================================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": base.BASE_DIR / "db.sqlite3",
    }
}

# =============================================================================
# DJANGO REST FRAMEWORK
# =============================================================================

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

# =============================================================================
# REQUIRED DJANGO SETTINGS (re-export)
# =============================================================================

BASE_DIR = base.BASE_DIR
SECRET_KEY = base.SECRET_KEY
INSTALLED_APPS = base.INSTALLED_APPS
MIDDLEWARE = base.MIDDLEWARE
ROOT_URLCONF = base.ROOT_URLCONF
WSGI_APPLICATION = base.WSGI_APPLICATION
LANGUAGE_CODE = base.LANGUAGE_CODE
TIME_ZONE = base.TIME_ZONE
USE_I18N = base.USE_I18N
USE_TZ = base.USE_TZ
STATIC_URL = base.STATIC_URL
STATIC_ROOT = base.STATIC_ROOT
DEFAULT_AUTO_FIELD = base.DEFAULT_AUTO_FIELD
