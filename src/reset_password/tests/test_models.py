from datetime import timedelta

import pytest
from django.utils import timezone

from reset_password.models import PasswordResetCode


@pytest.mark.django_db
def test_password_reset_code_is_valid(normal_user):
    reset = PasswordResetCode.objects.create(
        user=normal_user,
        code="123456",
        expires_at=timezone.now() + timedelta(minutes=5),
    )

    assert reset.is_valid() is True


@pytest.mark.django_db
def test_password_reset_code_expired(normal_user):
    reset = PasswordResetCode.objects.create(
        user=normal_user,
        code="123456",
        expires_at=timezone.now() - timedelta(minutes=1),
    )

    assert reset.is_valid() is False
