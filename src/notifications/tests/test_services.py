import pytest
from django.core import mail

from notifications.services import send_reset_password_code, send_welcome_email

# =========================
# WELCOME EMAIL
# =========================


@pytest.mark.django_db
def test_send_welcome_email(normal_user):
    password = "TestPassword123!"

    send_welcome_email(normal_user, password)

    assert len(mail.outbox) == 1

    email = mail.outbox[0]

    assert email.subject == "Bienvenue chez PrimeBank"

    assert normal_user.email in email.to

    assert email.alternatives
    html_content = email.alternatives[0][0]

    assert normal_user.first_name in html_content
    assert normal_user.email in html_content
    assert password in html_content


# =========================
# RESET PASSWORD CODE
# =========================


@pytest.mark.django_db
def test_send_reset_password_code(normal_user):
    code = "123456"

    send_reset_password_code(normal_user, code)

    assert len(mail.outbox) == 1

    email = mail.outbox[0]

    assert email.subject == "Code de vérification – PrimeBank"
    assert normal_user.email in email.to

    assert email.alternatives
    html_content = email.alternatives[0][0]

    assert normal_user.first_name in html_content
    assert code in html_content
    assert "10" in html_content  # expiration minutes
