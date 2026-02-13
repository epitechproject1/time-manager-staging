import pytest

from reset_password.models import PasswordResetCode
from reset_password.services import create_and_send_reset_code, verify_reset_code


@pytest.mark.django_db
def test_create_and_send_reset_code(normal_user):
    reset = create_and_send_reset_code(normal_user)

    assert isinstance(reset, PasswordResetCode)
    assert reset.user == normal_user
    assert reset.code is not None
    assert reset.is_used is False


@pytest.mark.django_db
def test_verify_reset_code_valid(normal_user):
    reset = PasswordResetCode.objects.create(
        user=normal_user,
        code="111111",
        expires_at=PasswordResetCode.generate_expiration(),
    )

    result = verify_reset_code(normal_user, "111111")

    assert result == reset


@pytest.mark.django_db
def test_verify_reset_code_invalid(normal_user):
    result = verify_reset_code(normal_user, "000000")

    assert result is None
