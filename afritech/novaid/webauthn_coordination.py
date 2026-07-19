"""Redis coordination for cross-process WebAuthn challenge state."""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any

from .observability import NovaIDMetrics


class WebAuthnCoordinationError(RuntimeError):
    pass


@dataclass(frozen=True)
class WebAuthnChallengeResult:
    status: str
    version: int | None = None
    challenge_id: str | None = None
    reason: str | None = None


class RedisWebAuthnChallengeCoordinator:
    """Redis fast-path coordination for challenge state.

    PostgreSQL remains authoritative; Redis mirrors advisory challenge state so
    other application processes can reject superseded or consumed challenges
    before the durable verification path reaches the database.
    """

    ACTIVE_STATUSES = {"ACTIVE", "SUPERSEDED", "CONSUMED", "EXPIRED", "CANCELLED"}

    CREATE_SCRIPT = """
local active_key = KEYS[1]
local challenge_key = KEYS[2]
local tenant_ref = ARGV[1]
local subject = ARGV[2]
local purpose = ARGV[3]
local challenge_hash = ARGV[4]
local ttl_seconds = tonumber(ARGV[5])
local now_epoch = tonumber(ARGV[6])
local previous_key = redis.call('GET', active_key)
if previous_key and previous_key ~= challenge_key then
  local previous_exists = redis.call('EXISTS', previous_key)
  if previous_exists == 1 then
    local previous_status = redis.call('HGET', previous_key, 'status')
    if previous_status == 'ACTIVE' then
      local previous_version = tonumber(redis.call('HGET', previous_key, 'version') or '1')
      redis.call('HSET', previous_key,
        'status', 'SUPERSEDED',
        'version', tostring(previous_version + 1),
        'updated_at_epoch', tostring(now_epoch)
      )
    end
  end
end
redis.call('HSET', challenge_key,
  'tenant_ref', tenant_ref,
  'subject', subject,
  'purpose', purpose,
  'challenge_id', string.match(challenge_key, '([^:]+)$'),
  'status', 'ACTIVE',
  'version', '1',
  'challenge_hash', challenge_hash,
  'created_at_epoch', tostring(now_epoch),
  'updated_at_epoch', tostring(now_epoch)
)
redis.call('EXPIRE', challenge_key, ttl_seconds)
redis.call('SET', active_key, challenge_key, 'EX', ttl_seconds)
return {'CREATED', challenge_key}
"""

    CONSUME_SCRIPT = """
local key = KEYS[1]
local expected_hash = ARGV[1]
local expected_version = ARGV[2]
local now_epoch = tonumber(ARGV[3])
local status = redis.call('HGET', key, 'status')
if not status then return {'NOT_FOUND'} end
local version = tonumber(redis.call('HGET', key, 'version') or '0')
local challenge_hash = redis.call('HGET', key, 'challenge_hash')
if expected_version ~= '' and version ~= tonumber(expected_version) then
  return {'VERSION_CONFLICT', tostring(version)}
end
if challenge_hash ~= expected_hash then
  return {'INVALID_STATE', status}
end
if status == 'CONSUMED' then return {'ALREADY_CONSUMED', tostring(version)} end
if status == 'SUPERSEDED' then return {'SUPERSEDED', tostring(version)} end
if status == 'EXPIRED' then return {'EXPIRED', tostring(version)} end
if status == 'CANCELLED' then return {'INVALID_STATE', tostring(version)} end
if status ~= 'ACTIVE' then return {'INVALID_STATE', tostring(version)} end
redis.call('HSET', key,
  'status', 'CONSUMED',
  'version', tostring(version + 1),
  'updated_at_epoch', tostring(now_epoch),
  'consumed_at_epoch', tostring(now_epoch)
)
return {'CONSUMED', tostring(version + 1)}
"""

    TOGGLE_SCRIPT = """
local key = KEYS[1]
local target_status = ARGV[1]
local expected_status = ARGV[2]
local now_epoch = tonumber(ARGV[3])
local status = redis.call('HGET', key, 'status')
if not status then return {'NOT_FOUND'} end
if status ~= expected_status then
  return {status, redis.call('HGET', key, 'version') or '0'}
end
local version = tonumber(redis.call('HGET', key, 'version') or '0')
redis.call('HSET', key,
  'status', target_status,
  'version', tostring(version + 1),
  'updated_at_epoch', tostring(now_epoch)
)
return {target_status, tostring(version + 1)}
"""

    def __init__(self, redis_client: Any, *, required: bool = False, metrics=None) -> None:
        self.redis, self.required = redis_client, required
        self.metrics = metrics or NovaIDMetrics()

    @staticmethod
    def _challenge_key(tenant_id: str, challenge_id: str, purpose: str = "webauthn") -> str:
        return f"novaid:v1:tenant:{tenant_id}:webauthn:{purpose}:{challenge_id}"

    @staticmethod
    def _active_key(tenant_id: str, subject: str, purpose: str) -> str:
        return f"novaid:v1:tenant:{tenant_id}:webauthn:active:{purpose}:{subject}"

    @staticmethod
    def _decode(result: Any) -> WebAuthnChallengeResult:
        if isinstance(result, (bytes, bytearray)):
            result = result.decode()
        if isinstance(result, str):
            return WebAuthnChallengeResult(status=result)
        if isinstance(result, (list, tuple)) and result:
            status = result[0]
            if isinstance(status, (bytes, bytearray)):
                status = status.decode()
            version = None
            challenge_id = None
            reason = None
            if len(result) > 1 and result[1] is not None:
                value = result[1]
                if isinstance(value, (bytes, bytearray)):
                    value = value.decode()
                if isinstance(value, str) and value.isdigit():
                    version = int(value)
                else:
                    challenge_id = str(value)
            if len(result) > 2 and result[2] is not None:
                value = result[2]
                if isinstance(value, (bytes, bytearray)):
                    value = value.decode()
                reason = str(value)
            return WebAuthnChallengeResult(
                status=str(status),
                version=version,
                challenge_id=challenge_id,
                reason=reason,
            )
        return WebAuthnChallengeResult(status=str(result))

    def _invoke(self, script: str, keys: list[str], argv: list[str], *, outcome: str) -> Any:
        try:
            result = self.redis.register_script(script)(keys=keys, args=argv)
            self.metrics.increment("novaid_webauthn_redis_challenge_total", outcome=outcome)
            return result
        except Exception as exc:
            self.metrics.increment("novaid_webauthn_redis_failures_total", outcome=outcome)
            if self.required:
                raise WebAuthnCoordinationError("WEBAUTHN_COORDINATION_UNAVAILABLE") from exc
            return WebAuthnChallengeResult(status=outcome.upper())

    def create(
        self,
        *,
        tenant_id: str,
        subject: str,
        purpose: str,
        challenge_id: str,
        challenge_hash: str,
        ttl_seconds: int,
    ) -> WebAuthnChallengeResult:
        now_epoch = str(int(time.time()))
        active_key = self._active_key(tenant_id, subject, purpose)
        challenge_key = self._challenge_key(tenant_id, challenge_id, purpose)
        result = self._invoke(
            self.CREATE_SCRIPT,
            [active_key, challenge_key],
            [tenant_id, subject, purpose, challenge_hash, str(ttl_seconds), now_epoch],
            outcome="created",
        )
        decoded = self._decode(result)
        if decoded.status == "CREATED":
            return WebAuthnChallengeResult(
                status="CREATED",
                challenge_id=challenge_id,
                reason=decoded.reason,
            )
        return decoded if decoded.status else WebAuthnChallengeResult(status="CREATED")

    def supersede(
        self,
        *,
        tenant_id: str,
        challenge_id: str,
        purpose: str = "webauthn",
    ) -> WebAuthnChallengeResult:
        now_epoch = str(int(time.time()))
        result = self._invoke(
            self.TOGGLE_SCRIPT,
            [self._challenge_key(tenant_id, challenge_id, purpose)],
            ["SUPERSEDED", "ACTIVE", now_epoch],
            outcome="superseded",
        )
        return self._decode(result)

    def invalidate(
        self,
        *,
        tenant_id: str,
        challenge_id: str,
        purpose: str = "webauthn",
        target_status: str = "EXPIRED",
    ) -> WebAuthnChallengeResult:
        if target_status not in {"EXPIRED", "CANCELLED"}:
            raise ValueError("invalid_challenge_terminal_state")
        now_epoch = str(int(time.time()))
        result = self._invoke(
            self.TOGGLE_SCRIPT,
            [self._challenge_key(tenant_id, challenge_id, purpose)],
            [target_status, "ACTIVE", now_epoch],
            outcome=target_status.lower(),
        )
        return self._decode(result)

    def consume(
        self,
        *,
        tenant_id: str,
        challenge_id: str,
        challenge_hash: str,
        expected_version: int | None = None,
        purpose: str = "webauthn",
    ) -> WebAuthnChallengeResult:
        now_epoch = str(int(time.time()))
        result = self._invoke(
            self.CONSUME_SCRIPT,
            [self._challenge_key(tenant_id, challenge_id, purpose)],
            [challenge_hash, str(expected_version or ""), now_epoch],
            outcome="consumed",
        )
        return self._decode(result)
