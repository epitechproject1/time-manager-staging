from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone


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
