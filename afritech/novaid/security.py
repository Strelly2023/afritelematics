"""Security primitives for NovaID authentication.

The module intentionally contains no transport or UI concerns.  Secrets are stored
only as salted, one-way verifiers and every consumable token is purpose bound.
Production deployments should replace the in-process stores with transactional
PostgreSQL/Redis adapters while preserving these state-machine invariants.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
import hashlib
import hmac
import secrets
from threading import RLock
from typing import Callable


Clock = Callable[[], datetime]


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _digest(secret: str, pepper: bytes) -> str:
    return hmac.new(pepper, secret.encode("utf-8"), hashlib.sha256).hexdigest()


class PasswordHasher:
    """Memory-hard scrypt password hashing with an upgradeable wire format."""

    def __init__(self, *, n: int = 2**14, r: int = 8, p: int = 1) -> None:
        if n < 2**14 or n & (n - 1):
            raise ValueError("scrypt_n_must_be_power_of_two_and_at_least_16384")
        self.n, self.r, self.p = n, r, p

    def hash(self, password: str) -> str:
        if len(password) < 12:
            raise ValueError("password_too_short")
        salt = secrets.token_bytes(16)
        result = hashlib.scrypt(password.encode(), salt=salt, n=self.n, r=self.r, p=self.p)
        return f"scrypt${self.n}${self.r}${self.p}${salt.hex()}${result.hex()}"

    def verify(self, password: str, encoded: str) -> bool:
        try:
            algorithm, n, r, p, salt, expected = encoded.split("$")
            if algorithm != "scrypt":
                return False
            actual = hashlib.scrypt(
                password.encode(), salt=bytes.fromhex(salt), n=int(n), r=int(r), p=int(p)
            )
            return hmac.compare_digest(actual, bytes.fromhex(expected))
        except (ValueError, TypeError):
            return False


@dataclass
class _OTP:
    digest: str
    identity_id: str
    purpose: str
    expires_at: datetime
    attempts_left: int
    used: bool = False


class OTPStore:
    PURPOSES = frozenset(
        {"registration", "login", "mfa", "recovery", "contact_change", "high_risk_action"}
    )

    def __init__(self, *, pepper: bytes | None = None, clock: Clock = _utcnow) -> None:
        self._pepper = pepper or secrets.token_bytes(32)
        self._clock = clock
        self._records: dict[str, _OTP] = {}
        self._lock = RLock()

    def issue(self, identity_id: str, purpose: str, *, ttl_seconds: int = 300) -> tuple[str, str]:
        if purpose not in self.PURPOSES:
            raise ValueError("invalid_otp_purpose")
        if not 30 <= ttl_seconds <= 600:
            raise ValueError("invalid_otp_ttl")
        code = f"{secrets.randbelow(1_000_000):06d}"
        otp_id = secrets.token_urlsafe(18)
        self._records[otp_id] = _OTP(
            _digest(f"{otp_id}:{identity_id}:{purpose}:{code}", self._pepper),
            identity_id,
            purpose,
            self._clock() + timedelta(seconds=ttl_seconds),
            5,
        )
        return otp_id, code

    def consume(self, otp_id: str, code: str, identity_id: str, purpose: str) -> bool:
        with self._lock:
            record = self._records.get(otp_id)
            if not record or record.used or record.expires_at <= self._clock():
                return False
            if record.identity_id != identity_id or record.purpose != purpose:
                return False
            record.attempts_left -= 1
            supplied = _digest(f"{otp_id}:{identity_id}:{purpose}:{code}", self._pepper)
            valid = record.attempts_left >= 0 and hmac.compare_digest(record.digest, supplied)
            if valid:
                record.used = True
            return valid


@dataclass
class RefreshFamily:
    identity_id: str
    session_id: str
    expires_at: datetime
    current_digest: str
    revoked: bool = False
    used_digests: set[str] = field(default_factory=set)


class RefreshTokenStore:
    """Rotating refresh families; reuse atomically revokes the whole family."""

    def __init__(self, *, pepper: bytes | None = None, clock: Clock = _utcnow) -> None:
        self._pepper = pepper or secrets.token_bytes(32)
        self._clock = clock
        self._families: dict[str, RefreshFamily] = {}
        self._lock = RLock()

    def issue(self, identity_id: str, session_id: str, *, ttl_days: int = 30) -> str:
        family_id, secret = secrets.token_urlsafe(18), secrets.token_urlsafe(32)
        self._families[family_id] = RefreshFamily(
            identity_id,
            session_id,
            self._clock() + timedelta(days=ttl_days),
            _digest(secret, self._pepper),
        )
        return f"{family_id}.{secret}"

    def rotate(self, token: str) -> str | None:
        try:
            family_id, secret = token.split(".", 1)
        except ValueError:
            return None
        supplied = _digest(secret, self._pepper)
        with self._lock:
            family = self._families.get(family_id)
            if not family or family.revoked or family.expires_at <= self._clock():
                return None
            if supplied in family.used_digests:
                family.revoked = True
                return None
            if not hmac.compare_digest(supplied, family.current_digest):
                return None
            family.used_digests.add(family.current_digest)
            new_secret = secrets.token_urlsafe(32)
            family.current_digest = _digest(new_secret, self._pepper)
            return f"{family_id}.{new_secret}"

    def revoke_session(self, session_id: str) -> int:
        with self._lock:
            matches = [
                family
                for family in self._families.values()
                if family.session_id == session_id and not family.revoked
            ]
            for family in matches:
                family.revoked = True
            return len(matches)
