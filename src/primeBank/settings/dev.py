from datetime import timedelta

from .base import *  # noqa

# =============================================================================
# GENERAL
# =============================================================================

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# =============================================================================
# CORS (CRUCIAL POUR TON REACT)
# =============================================================================

# Ici, on surcharge la config de base pour être sûr que le dev fonctionne
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",  # Vite (localhost)
    "http://127.0.0.1:5173",  # Vite (IP)
]

CORS_ALLOW_CREDENTIALS = True

# =============================================================================
# DRF & AUTHENTICATION
# =============================================================================

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# =============================================================================
# SIMPLE JWT (Configuration des tokens)
# =============================================================================

SIMPLE_JWT = {
    # On met 60 minutes pour le dev pour ne pas devoir se reloguer tout le temps
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# =============================================================================
# DOCUMENTATION (Spectacular / Swagger)
# =============================================================================

SPECTACULAR_SETTINGS = {
    "TITLE": "PrimeBank API",
    "DESCRIPTION": "Documentation de l'API pour le projet PrimeBank",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    # Pour que le bouton "Authorize" apparaisse dans Swagger
    "COMPONENT_SPLIT_REQUEST": True,
}

# =============================================================================
# EMAILS (Console)
# =============================================================================

# Affiche les emails dans la console au lieu de les envoyer réellement
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
