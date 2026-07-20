from datetime import UTC, datetime, timedelta

from afritech.novaid.security import OTPStore, PasswordHasher, RefreshTokenStore


def test_passwords_are_salted_and_one_way() -> None:
    hasher = PasswordHasher()
    first = hasher.hash("a sufficiently strong password")
    second = hasher.hash("a sufficiently strong password")
    assert first != second
    assert "sufficiently" not in first
    assert hasher.verify("a sufficiently strong password", first)
    assert not hasher.verify("wrong password", first)


def test_otp_is_purpose_bound_single_use_and_expires() -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    store = OTPStore(pepper=b"test" * 8, clock=lambda: now)
    otp_id, code = store.issue("id-1", "registration")
    assert not store.consume(otp_id, code, "id-1", "login")
    assert store.consume(otp_id, code, "id-1", "registration")
    assert not store.consume(otp_id, code, "id-1", "registration")

    expired = OTPStore(pepper=b"test" * 8, clock=lambda: now)
    expired_id, expired_code = expired.issue("id-1", "mfa", ttl_seconds=30)
    expired._clock = lambda: now + timedelta(seconds=31)
    assert not expired.consume(expired_id, expired_code, "id-1", "mfa")


def test_refresh_rotation_reuse_revokes_family_and_session_revocation_is_immediate() -> None:
    store = RefreshTokenStore(pepper=b"test" * 8)
    original = store.issue("id-1", "session-1")
    rotated = store.rotate(original)
    assert rotated is not None
    assert store.rotate(original) is None
    assert store.rotate(rotated) is None

    second = store.issue("id-1", "session-2")
    assert store.revoke_session("session-2") == 1
    assert store.rotate(second) is None
