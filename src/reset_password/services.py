import random

from notifications.services import send_reset_password_code

from .models import PasswordResetCode


# =========================
# CREATE + SEND CODE
# =========================
def create_and_send_reset_code(user):
    """
    Génère un code OTP, invalide les anciens et l'envoie par email.
    """

    # 🔒 Invalider anciens codes actifs
    PasswordResetCode.objects.filter(
        user=user,
        is_used=False,
    ).update(is_used=True)

    # 🔢 Génération code 6 chiffres
    code = f"{random.randint(0, 999999):06d}"

    # 🕒 Création en DB
    reset_code = PasswordResetCode.objects.create(
        user=user,
        code=code,
        expires_at=PasswordResetCode.generate_expiration(),
    )

    # 📧 Envoi email
    send_reset_password_code(user, code)

    return reset_code


# =========================
# VERIFY CODE
# =========================
def verify_reset_code(user, code):
    """
    Vérifie qu'un code est valide.
    """

    try:
        reset = PasswordResetCode.objects.get(
            user=user,
            code=code,
            is_used=False,
        )
    except PasswordResetCode.DoesNotExist:
        return None

    if not reset.is_valid():
        return None

    return reset
