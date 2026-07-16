"""Runtime verification runner."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
import uuid

from .probes import VerificationContext, VerificationProbe, VerificationProbeResult, build_reference_probes


@dataclass(frozen=True, slots=True)
class VerificationRun:
    verification_id: str
    product_code: str
    status: str
    probe_results: tuple[VerificationProbeResult, ...]
    started_at: str
    completed_at: str
    evidence: dict[str, Any]


class RuntimeVerificationService:
    def __init__(self, probes: tuple[VerificationProbe, ...] | None = None) -> None:
        self.probes = probes or ()

    async def run(self, context: VerificationContext) -> VerificationRun:
        probes = self.probes or build_reference_probes(context.product_code)
        started = datetime.now(timezone.utc)
        results = tuple([await probe.execute(context) for probe in probes])
        status = "PASS" if all(result.status == "PASS" for result in results if result.probe_id.endswith(("health", "ready", "products", "workers", "platform", "synthetic-command"))) else "FAIL"
        return VerificationRun(f"verification-{uuid.uuid4().hex[:12]}", context.product_code, status, results, started.isoformat(), datetime.now(timezone.utc).isoformat(), {"result_count": len(results)})

