from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

EXPIRY_MINUTES = settings.EXPIRY_MINUTES


def send_welcome_email(user, password):
    """
    Envoie un email de bienvenue (HTML uniquement).
    """

    context = {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "password": password,
        "year": timezone.now().year,
    }

    subject = "Bienvenue chez PrimeBank"

    html_content = render_to_string("emails/welcome.html", context)

    email = EmailMultiAlternatives(
        subject=subject,
        body=html_content,  # fallback texte = HTML
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )

    email.attach_alternative(html_content, "text/html")
    email.send(fail_silently=False)


def send_reset_password_code(user, code):
    context = {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "verification_code": code,
        "expiration_minutes": 10,
        "year": timezone.now().year,
    }

    subject = "Code de vérification – PrimeBank"

    html_content = render_to_string(
        "emails/reset_password_code.html",
        context,
    )

    email = EmailMultiAlternatives(
        subject=subject,
        body=html_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )

    email.attach_alternative(html_content, "text/html")
    email.send(fail_silently=False)


def send_clock_validation_code(user, code, event_type, expires_at):
    """
    Envoie le code de validation de pointage (clock-in ou clock-out).
    """

    # 🧠 Libellé lisible pour l'utilisateur
    event_label = {
        "CLOCK_IN": "entrée",
        "CLOCK_OUT": "sortie",
    }.get(event_type, "pointage")

    context = {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "verification_code": code,
        "event_type": event_label,
        "expires_at": expires_at,
        "expiration_minutes": EXPIRY_MINUTES,
        "year": timezone.now().year,
    }

    subject = f"Code de validation de pointage ({event_label})"

    html_content = render_to_string(
        "emails/clock_validation_code.html",
        context,
    )

    email = EmailMultiAlternatives(
        subject=subject,
        body=html_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )

    email.attach_alternative(html_content, "text/html")
    email.send(fail_silently=False)
