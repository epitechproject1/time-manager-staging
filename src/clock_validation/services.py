from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone


def send_clock_validation_code(user, code, event_type: str, expires_at):
    """
    Envoie le code de validation de pointage par email.

    :param user:        Instance utilisateur
    :param code:        Code à 6 chiffres
    :param event_type:  "CLOCK_IN" ou "CLOCK_OUT"
    :param expires_at:  datetime d'expiration du code
    """

    event_label = "début de shift" if event_type == "CLOCK_IN" else "fin de shift"

    context = {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "code": code,
        "event_label": event_label,
        "expires_at": expires_at,
        "expiration_minutes": settings.EXPIRY_MINUTES,
        "year": timezone.now().year,
    }

    subject = f"Code de validation — {event_label.capitalize()} · PrimeBank"

    html_content = render_to_string("emails/clock_validation_code.html", context)

    email = EmailMultiAlternatives(
        subject=subject,
        body=html_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )

    email.attach_alternative(html_content, "text/html")
    email.send(fail_silently=False)
