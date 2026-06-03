from __future__ import annotations

from copy import deepcopy
from typing import Any

from afritech.security.event_authenticator import EventAuthenticator
from afritech.security.integrity_trace import IntegrityTrace
from afritech.security.mutation_guard import MutationGuard


class AdversarialEngine:
    """AUTHENTICITY -> STRUCTURE -> LINEAGE -> ADMISSIBILITY gate."""

    def __init__(
        self,
        authenticator: EventAuthenticator,
        guard: MutationGuard,
        secret: str,
        *,
        trusted_lineage_roots: set[str] | None = None,
    ) -> None:
        self.authenticator = authenticator
        self.guard = guard
        self.secret = secret
        self.trusted_lineage_roots = set(trusted_lineage_roots or set())
        self._seen_fingerprints: set[str] = set()

    def process(self, event: dict[str, Any], signature: str) -> dict[str, Any]:
        self.guard.require_valid(event)

        if not self.authenticator.verify(event, signature, self.secret):
            raise ValueError("Authentication failed")

        self._require_trusted_lineage(event)

        fingerprint = IntegrityTrace.mutation_fingerprint(event)
        if fingerprint in self._seen_fingerprints:
            raise ValueError("Replay mutation detected")
        self._seen_fingerprints.add(fingerprint)

        admitted = deepcopy(dict(event))
        admitted["integrity_hash"] = IntegrityTrace.hash_event(
            {
                "id": admitted["id"],
                "lineage": tuple(admitted.get("lineage", ())),
                "payload": admitted["payload"],
                "timestamp": admitted["timestamp"],
            }
        )
        admitted["security_trace"] = {
            "stages": [
                "authenticity",
                "structure",
                "lineage",
                "admissibility",
            ],
            "status": "admitted_authenticated_mutation",
        }
        return admitted

    def _require_trusted_lineage(self, event: dict[str, Any]) -> None:
        lineage = tuple(event.get("lineage", ()))
        if not self.trusted_lineage_roots:
            return
        if not lineage or lineage[0] not in self.trusted_lineage_roots:
            raise ValueError("Lineage validation failed")
