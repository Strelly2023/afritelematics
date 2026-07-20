#!/usr/bin/env python3
"""Live operational verification for NovaID Phase 6F part 2.

This drives the real local NovaID HTTP servers, the shared PostgreSQL database,
and the shared Redis database. It is intentionally explicit and evidence-friendly.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass, asdict
from datetime import UTC, datetime
import hashlib
import json
import hmac
import os
from pathlib import Path
import time
from uuid import uuid4

import cbor2
import httpx
import psycopg
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec


def uid() -> str:
    return str(uuid4())


def b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


class VirtualAuthenticator:
    def __init__(self, *, origin: str = "http://localhost") -> None:
        self.origin = origin
        self.key = ec.generate_private_key(ec.SECP256R1())
        self.credential_id = uuid4().bytes
        self.sign_count = 0

    def registration(self, challenge: str, *, origin: str | None = None) -> dict[str, object]:
        origin = origin or self.origin
        numbers = self.key.public_key().public_numbers()
        cose = cbor2.dumps(
            {1: 2, 3: -7, -1: 1, -2: numbers.x.to_bytes(32, "big"), -3: numbers.y.to_bytes(32, "big")}
        )
        auth_data = (
            hashlib.sha256(b"localhost").digest()
            + bytes([0x45])
            + (0).to_bytes(4, "big")
            + bytes(16)
            + len(self.credential_id).to_bytes(2, "big")
            + self.credential_id
            + cose
        )
        client = json.dumps(
            {"type": "webauthn.create", "challenge": challenge, "origin": origin},
            separators=(",", ":"),
        ).encode()
        return {
            "id": b64(self.credential_id),
            "rawId": b64(self.credential_id),
            "type": "public-key",
            "response": {
                "clientDataJSON": b64(client),
                "attestationObject": b64(
                    cbor2.dumps({"fmt": "none", "attStmt": {}, "authData": auth_data})
                ),
                "transports": ["internal"],
            },
        }

    def assertion(self, challenge: str, *, origin: str | None = None) -> dict[str, object]:
        origin = origin or self.origin
        self.sign_count += 1
        auth_data = hashlib.sha256(b"localhost").digest() + bytes([0x05]) + self.sign_count.to_bytes(4, "big")
        client = json.dumps(
            {"type": "webauthn.get", "challenge": challenge, "origin": origin},
            separators=(",", ":"),
        ).encode()
        signature = self.key.sign(auth_data + hashlib.sha256(client).digest(), ec.ECDSA(hashes.SHA256()))
        return {
            "id": b64(self.credential_id),
            "rawId": b64(self.credential_id),
            "type": "public-key",
            "response": {
                "clientDataJSON": b64(client),
                "authenticatorData": b64(auth_data),
                "signature": b64(signature),
                "userHandle": None,
            },
        }


@dataclass
class StepResult:
    name: str
    status: int
    code: str | None = None
    detail: str | None = None


class Probe:
    def __init__(self) -> None:
        self.base_a = os.getenv("NOVAID_BASE_URL_A", "http://127.0.0.1:58601")
        self.base_b = os.getenv("NOVAID_BASE_URL_B", "http://127.0.0.1:58602")
        self.origin_a = self.base_a.replace("127.0.0.1", "localhost")
        self.origin_b = self.base_b.replace("127.0.0.1", "localhost")
        self.dsn = os.getenv("NOVAID_DATABASE_URL", "")
        self.tenant_a = os.getenv("NOVAID_PHASE6F_TENANT_A", "710a798a-7a55-4329-a314-5a619059d376")
        self.tenant_b = os.getenv("NOVAID_PHASE6F_TENANT_B", "a8b72d5d-c109-49b1-b818-e36efe6ea294")
        self.event_path = Path("deployment-evidence/security-distributed-runtime")
        self.event_path.mkdir(parents=True, exist_ok=True)
        self.steps: list[StepResult] = []
        self.summary: dict[str, object] = {}
        self.admin_token = ""
        self.access_token = ""
        self.refresh_token = ""
        self.stepup_token = ""
        self.passwordless_access_token = ""
        self.identity_id = ""
        self.email = f"phase6f.operator.{uuid4().hex}@example.com"
        self.membership_id = ""
        self.session_id = ""
        self.challenge_id = ""
        self.verification_code = ""
        self.authenticator: VirtualAuthenticator | None = None
        self.credential_id = ""
        self.webauthn_registration_challenge_a = ""
        self.webauthn_registration_challenge_b = ""
        self.webauthn_auth_challenge_a = ""
        self.webauthn_auth_challenge_b = ""
        self.replay_request_id = ""
        self.dry_run_replay = {}
        self.operator_id = str(uuid4())
        self.approver_id = str(uuid4())
        self.approver_token = ""

    def _client(self, base: str) -> httpx.Client:
        return httpx.Client(base_url=base, timeout=20.0)

    def _record(self, name: str, response: httpx.Response, *, code: str | None = None) -> None:
        detail = None
        try:
            body = response.json()
            detail = json.dumps(body, sort_keys=True)[:300]
            if code is None and isinstance(body, dict):
                code = body.get("code") or body.get("detail", {}).get("code")  # type: ignore[union-attr]
        except Exception:
            detail = response.text[:300]
        self.steps.append(StepResult(name=name, status=response.status_code, code=code, detail=detail))

    def _mint_token(self, subject: str) -> str:
        secret = os.getenv("AFRITECH_JWT_SECRET")
        if not secret:
            raise RuntimeError("AFRITECH_JWT_SECRET_required_for_operational_probe")
        header = {"alg": "HS256", "typ": "JWT"}
        payload = {
            "sub": subject,
            "role": "ADMIN",
            "organization_id": self.tenant_a,
            "tenant_id": self.tenant_a,
            "permissions": [
                "audit.events.read",
                "audit.events.read_sensitive",
                "audit.events.export",
                "audit.checkpoints.read",
                "audit.dead_letters.read",
                "audit.replay.request",
                "audit.replay.approve",
                "audit.replay.execute",
                "audit.replay.cancel",
                "audit.replay.verify",
                "audit.replay.evidence.read",
            ],
            "exp": int(time.time()) + 3600,
            "token_kind": "access",
        }
        encoded_header = b64(json.dumps(header, sort_keys=True, separators=(",", ":")).encode())
        encoded_payload = b64(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode())
        signing_input = f"{encoded_header}.{encoded_payload}".encode()
        signature = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
        return f"{encoded_header}.{encoded_payload}.{b64(signature)}"

    def seed_operator_token(self) -> None:
        self.admin_token = self._mint_token(self.operator_id)
        self.approver_token = self._mint_token(self.approver_id)

    def ensure_policy_actor(self) -> None:
        if not self.membership_id:
            raise RuntimeError("membership_id_required_for_governed_policy_update")
        with psycopg.connect(self.dsn) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE novaid_tenant_memberships SET role='ADMIN', updated_at=NOW() "
                    "WHERE tenant_id=%s AND membership_id=%s AND status='ACTIVE'",
                    (self.tenant_a, self.membership_id),
                )
                if cursor.rowcount != 1:
                    raise RuntimeError("policy_actor_promotion_failed")
                connection.commit()

    def load_membership_id(self) -> None:
        if self.membership_id:
            return
        with psycopg.connect(self.dsn) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT membership_id FROM novaid_authentication_sessions "
                    "WHERE tenant_id=%s AND identity_id=%s AND session_id=%s",
                    (self.tenant_a, self.identity_id, self.session_id),
                )
                row = cursor.fetchone()
                if not row:
                    raise RuntimeError("membership_id_lookup_failed")
                self.membership_id = str(row[0])

    def health(self) -> None:
        with self._client(self.base_a) as a, self._client(self.base_b) as b:
            for name, client, route in (
                ("a_live", a, "/health/live"),
                ("a_ready", a, "/health/ready"),
                ("b_live", b, "/health/live"),
                ("b_ready", b, "/health/ready"),
            ):
                response = client.get(route)
                self._record(name, response)
                response.raise_for_status()

    def register_and_login(self) -> None:
        headers = {
            "x-tenant-id": self.tenant_a,
            "idempotency-key": uid(),
            "x-correlation-id": uid(),
            "x-request-id": uid(),
        }
        with self._client(self.base_a) as client:
            register = client.post(
                "/v1/novaid/register",
                headers=headers,
                json={
                    "email": self.email,
                    "password": "a strong phase6f registration password",
                },
            )
            self._record("register", register)
            register.raise_for_status()
            payload = register.json()
            self.identity_id = payload["identity_id"]
            self.challenge_id = payload["challenge_id"]
            self.verification_code = payload["verification_code"]

            verify = client.post(
                "/v1/novaid/verify",
                headers=headers,
                json={
                    "identity_id": self.identity_id,
                    "challenge_id": self.challenge_id,
                    "code": self.verification_code,
                },
            )
            self._record("verify", verify)
            verify.raise_for_status()

            login = client.post(
                "/v1/novaid/authenticate",
                headers=headers,
                json={
                    "email": self.email,
                    "password": "a strong phase6f registration password",
                },
            )
            self._record("authenticate", login)
            login.raise_for_status()
            payload = login.json()
            self.session_id = payload["session_id"]
            self.challenge_id = payload["challenge_id"]
            self.verification_code = payload["mfa_code"]

            mfa = client.post(
                "/v1/novaid/mfa/verify",
                headers=headers,
                json={
                    "session_id": self.session_id,
                    "challenge_id": self.challenge_id,
                    "code": self.verification_code,
                },
            )
            self._record("mfa_verify", mfa)
            mfa.raise_for_status()
            payload = mfa.json()
            self.access_token = payload["access_token"]
            self.refresh_token = payload["refresh_token"]
            self.membership_id = payload["membership_id"] if "membership_id" in payload else ""
            self.load_membership_id()

    def cross_process_session_and_refresh(self) -> None:
        headers = {
            "x-tenant-id": self.tenant_a,
            "authorization": f"Bearer {self.access_token}",
        }
        with self._client(self.base_b) as client:
            me = client.get("/v1/novaid/me", headers=headers)
            self._record("b_me", me)
            me.raise_for_status()
            refresh = client.post(
                "/v1/novaid/token/refresh",
                headers={
                    "x-tenant-id": self.tenant_a,
                    "x-correlation-id": uid(),
                    "x-request-id": uid(),
                },
                json={"refresh_token": self.refresh_token},
            )
            self._record("b_refresh", refresh)
            refresh.raise_for_status()
            self.refresh_token = refresh.json()["refresh_token"]

    def step_up_and_policy(self) -> None:
        headers = {
            "x-tenant-id": self.tenant_a,
            "authorization": f"Bearer {self.access_token}",
            "x-correlation-id": uid(),
            "x-request-id": uid(),
        }
        with self._client(self.base_a) as client:
            step_options = client.post(
                "/v1/novaid/webauthn/step-up/options",
                headers=headers,
                json={"session_id": self.session_id},
            )
            self._record("step_up_options", step_options)
            step_options.raise_for_status()
            challenge = step_options.json()["public_key"]["challenge"]
            self.webauthn_auth_challenge_a = challenge
            stepup = client.post(
                "/v1/novaid/webauthn/step-up/verify",
                headers=headers,
                json={
                    "session_id": self.session_id,
                    "challenge_id": step_options.json()["challenge_id"],
                    "credential": self.authenticator.assertion(challenge, origin=self.origin_a),
                },
            )
            self._record("step_up_verify", stepup)
            stepup.raise_for_status()
            self.stepup_token = stepup.json()["access_token"]
            self.ensure_policy_actor()
            policy = client.get(
                "/v1/novaid/webauthn/policy",
                headers={"x-tenant-id": self.tenant_a, "authorization": f"Bearer {self.stepup_token}"},
            )
            self._record("policy_get", policy)
            policy.raise_for_status()
            current = policy.json()
            allowed_policy_fields = {
                key: current[key]
                for key in (
                    "enabled",
                    "passkeys_enabled",
                    "passwordless_enabled",
                    "phishing_resistant_step_up_required",
                    "user_verification",
                    "attestation",
                    "maximum_credentials",
                    "recovery_codes_enabled",
                    "recovery_code_count",
                    "recovery_code_expiry_days",
                    "recovery_approval_count",
                    "recovery_requires_new_authenticator",
                    "step_up_seconds",
                )
                if key in current
            }
            updated = client.put(
                "/v1/novaid/webauthn/policy",
                headers={"x-tenant-id": self.tenant_a, "authorization": f"Bearer {self.stepup_token}"},
                json={
                    "policy": {
                        **allowed_policy_fields,
                        "step_up_seconds": int(current.get("step_up_seconds", 300)),
                    },
                    "expected_version": current.get("version") or None,
                    "reason": "Phase 6F operational verification",
                },
            )
            self._record("policy_put", updated)
            updated.raise_for_status()

    def challenge_supersession_and_registration(self) -> None:
        headers = {
            "x-tenant-id": self.tenant_a,
            "authorization": f"Bearer {self.access_token}",
            "x-correlation-id": uid(),
            "x-request-id": uid(),
        }
        with self._client(self.base_a) as a, self._client(self.base_b) as b:
            if self.authenticator is None:
                self.authenticator = VirtualAuthenticator()
            assert self.authenticator is not None
            first = a.post(
                "/v1/novaid/webauthn/registration/options",
                headers=headers,
                json={"user_name": self.email},
            )
            self._record("registration_options_a2", first)
            first.raise_for_status()
            first_challenge = first.json()
            second = b.post(
                "/v1/novaid/webauthn/registration/options",
                headers=headers,
                json={"user_name": self.email},
            )
            self._record("registration_options_b", second)
            second.raise_for_status()
            second_challenge = second.json()
            rejected = a.post(
                "/v1/novaid/webauthn/registration/verify",
                headers=headers,
                json={
                    "challenge_id": first_challenge["challenge_id"],
                    "credential": self.authenticator.registration(
                        first_challenge["public_key"]["challenge"], origin=self.origin_a
                    ),
                },
            )
            self._record("registration_verify_superseded", rejected)
            accepted = b.post(
                "/v1/novaid/webauthn/registration/verify",
                headers=headers,
                json={
                    "challenge_id": second_challenge["challenge_id"],
                    "credential": self.authenticator.registration(
                        second_challenge["public_key"]["challenge"], origin=self.origin_b
                    ),
                    "friendly_name": "Phase 6F virtual authenticator",
                },
            )
            self._record("registration_verify_active", accepted)
            if accepted.status_code != 201:
                print("registration_verify_active_failure", accepted.status_code, accepted.text)
            accepted.raise_for_status()
            self.credential_id = accepted.json()["credential_id"]

    def passwordless_flow(self) -> None:
        headers = {
            "x-tenant-id": self.tenant_a,
            "authorization": f"Bearer {self.stepup_token}",
            "x-correlation-id": uid(),
            "x-request-id": uid(),
        }
        with self._client(self.base_b) as client:
            options = client.post(
                "/v1/novaid/webauthn/authentication/options",
                headers=headers,
                json={"identity_id": self.identity_id, "session_id": None},
            )
            self._record("authentication_options_b", options)
            options.raise_for_status()
            challenge = options.json()["challenge_id"]
            assertion = self.authenticator.assertion(
                options.json()["public_key"]["challenge"], origin=self.origin_b
            )
            verified = client.post(
                "/v1/novaid/webauthn/passwordless/verify",
                headers=headers,
                json={"challenge_id": challenge, "credential": assertion},
            )
            self._record("passwordless_verify", verified)
            verified.raise_for_status()
            self.passwordless_access_token = verified.json()["access_token"]

    def replay_checks(self) -> None:
        with self._client(self.base_a) as client:
            unauthorized = client.get(
                "/api/v1/audit/replay/requests",
                headers={"x-tenant-id": self.tenant_a},
            )
            self._record("replay_unauthorized", unauthorized)

            read = client.get(
                "/api/v1/audit/replay/requests",
                headers={
                    "authorization": f"Bearer {self.admin_token}",
                    "x-tenant-id": self.tenant_a,
                },
            )
            self._record("replay_list", read)
            read.raise_for_status()
            request = client.post(
                "/api/v1/audit/replay/requests",
                headers={
                    "authorization": f"Bearer {self.admin_token}",
                    "x-tenant-id": self.tenant_a,
                },
                json={
                    "event_type_filters": ["IDENTITY_CREATED", "MFA_CHALLENGE_CREATED"],
                    "replay_mode": "dry_run",
                    "dry_run": True,
                    "reason": "Phase 6F operational verification",
                    "maximum_events": 25,
                    "correlation_id": uid(),
                    "request_id": uid(),
                },
            )
            self._record("replay_request", request)
            request.raise_for_status()
            self.replay_request_id = request.json()["replay_request_id"]
            evaluate = client.post(
                f"/api/v1/audit/replay/requests/{self.replay_request_id}/evaluate",
                headers={"authorization": f"Bearer {self.admin_token}", "x-tenant-id": self.tenant_a},
            )
            self._record("replay_evaluate", evaluate)
            evaluate.raise_for_status()
            approval_req = client.post(
                f"/api/v1/audit/replay/requests/{self.replay_request_id}/approval-requests",
                headers={"authorization": f"Bearer {self.admin_token}", "x-tenant-id": self.tenant_a},
                json={"reason": "Need operator approval"},
            )
            self._record("replay_approval_request", approval_req)
            approval_req.raise_for_status()
            approve = client.post(
                f"/api/v1/audit/replay/requests/{self.replay_request_id}/approve",
                headers={"authorization": f"Bearer {self.approver_token}", "x-tenant-id": self.tenant_a},
                json={"reason": "Approved for dry-run"},
            )
            self._record("replay_approve", approve)
            approve.raise_for_status()
            execute = client.post(
                f"/api/v1/audit/replay/requests/{self.replay_request_id}/execute",
                headers={"authorization": f"Bearer {self.approver_token}", "x-tenant-id": self.tenant_a},
                json={"reason": "Execute dry-run"},
            )
            self._record("replay_execute", execute)
            execute.raise_for_status()
            evidence = client.get(
                f"/api/v1/audit/replay/requests/{self.replay_request_id}/evidence",
                headers={"authorization": f"Bearer {self.admin_token}", "x-tenant-id": self.tenant_a},
            )
            self._record("replay_evidence", evidence)
            evidence.raise_for_status()
            checkpoints = client.get(
                "/api/v1/audit/checkpoints",
                headers={"authorization": f"Bearer {self.admin_token}", "x-tenant-id": self.tenant_a},
            )
            self._record("checkpoint_list", checkpoints)
            checkpoints.raise_for_status()
            dead_letters = client.get(
                "/api/v1/audit/dead-letters",
                headers={"authorization": f"Bearer {self.admin_token}", "x-tenant-id": self.tenant_a},
            )
            self._record("dead_letter_list", dead_letters)
            dead_letters.raise_for_status()
            self.dry_run_replay = {
                "request": request.json(),
                "evidence": evidence.json(),
            }

    def inspect_db(self) -> dict[str, object]:
        result: dict[str, object] = {}
        with psycopg.connect(self.dsn) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT status,authentication_strength,identity_id,membership_id,session_id "
                    "FROM novaid_authentication_sessions WHERE tenant_id=%s ORDER BY created_at DESC LIMIT 1",
                    (self.tenant_a,),
                )
                result["session"] = cursor.fetchone()
                cursor.execute(
                    "SELECT count(*) FROM novaid_webauthn_outbox WHERE tenant_id=%s",
                    (self.tenant_a,),
                )
                result["outbox_count"] = cursor.fetchone()[0]
                cursor.execute(
                    "SELECT count(*) FROM novaid_security_events WHERE tenant_id=%s",
                    (self.tenant_a,),
                )
                result["security_events"] = cursor.fetchone()[0]
                cursor.execute(
                    "SELECT count(*) FROM novaid_audit_replay_requests"
                )
                result["replay_requests"] = cursor.fetchone()[0]
        return result

    def run(self) -> dict[str, object]:
        self.seed_operator_token()
        self.health()
        self.register_and_login()
        self.cross_process_session_and_refresh()
        self.challenge_supersession_and_registration()
        self.step_up_and_policy()
        self.passwordless_flow()
        self.replay_checks()
        summary = {
            "tenant_a": self.tenant_a,
            "tenant_b": self.tenant_b,
            "identity_id": self.identity_id,
            "session_id": self.session_id,
            "credential_id": self.credential_id,
            "admin_token_scoped": bool(self.admin_token),
            "passwordless_access_token_scoped": bool(self.passwordless_access_token),
            "replay_request_id": self.replay_request_id,
            "db": self.inspect_db(),
            "steps": [asdict(step) for step in self.steps],
        }
        self.event_path.joinpath("phase6f_live_summary.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True, default=str)
        )
        return summary


def main() -> int:
    probe = Probe()
    summary = probe.run()
    print(json.dumps(summary, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
