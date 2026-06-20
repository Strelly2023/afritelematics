from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Event, Thread
from time import sleep
from typing import Any, Iterable
from uuid import uuid4

from afritech.afriprogramming.assurance.continuous_engine import ContinuousAssuranceService
from afritech.afriprogramming.persistence import DEFAULT_ORGANIZATION_ID, PlatformStore, get_platform_store
from afritech.afriprogramming.v9.schema import ensure_v9_schema


def _now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


@dataclass(frozen=True)
class SchedulerRun:
    scheduler_run_id: str
    organization_id: str
    scheduled_at: str
    executed_at: str
    status: str
    trust_score: int
    drift: int
    risk_score: int
    notes: str
    created_at: str


class AssuranceScheduler:
    """Run continuous assurance on a schedule and persist run history."""

    def __init__(
        self,
        repository: PlatformStore | None = None,
        assurance_service: ContinuousAssuranceService | None = None,
    ) -> None:
        self.repository = repository or get_platform_store()
        self.assurance_service = assurance_service or ContinuousAssuranceService(self.repository)
        self._stop = Event()
        self._worker: Thread | None = None
        ensure_v9_schema(self.repository)

    def run_once(self, organization_ids: Iterable[str] | None = None) -> list[dict[str, Any]]:
        targets = list(organization_ids) if organization_ids is not None else self._organizations()
        runs: list[dict[str, Any]] = []
        for organization_id in targets:
            scheduled_at = _now()
            run = self.assurance_service.run(organization_id=organization_id, actor_user_id="scheduler")
            record = {
                "scheduler_run_id": f"srun-{uuid4().hex[:12]}",
                "organization_id": organization_id,
                "scheduled_at": scheduled_at,
                "executed_at": _now(),
                "status": run["assurance_status"],
                "trust_score": int(run["trust_score"]),
                "drift": int(run["drift"]),
                "risk_score": int(run["risk_score"]),
                "notes": f"alert_level={run['alert_level']}",
                "created_at": _now(),
            }
            self._store_run(record)
            runs.append(record)
        return runs

    def start(self, *, interval_seconds: int = 300, organization_ids: Iterable[str] | None = None) -> None:
        if self._worker is not None and self._worker.is_alive():
            return

        def _loop() -> None:
            while not self._stop.is_set():
                self.run_once(organization_ids=organization_ids)
                self._stop.wait(interval_seconds)

        self._stop.clear()
        self._worker = Thread(target=_loop, daemon=True)
        self._worker.start()

    def stop(self) -> None:
        self._stop.set()
        if self._worker is not None and self._worker.is_alive():
            self._worker.join(timeout=2.0)

    def history(self, organization_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        query = "SELECT * FROM assurance_scheduler_runs"
        params: list[Any] = []
        if organization_id is not None:
            query += " WHERE organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self.repository._connect() as conn:  # noqa: SLF001 - repository boundary shim
            rows = conn.execute(query, params).fetchall()
        return [
            {
                "scheduler_run_id": row["scheduler_run_id"],
                "organization_id": row["organization_id"],
                "scheduled_at": row["scheduled_at"],
                "executed_at": row["executed_at"],
                "status": row["status"],
                "trust_score": row["trust_score"],
                "drift": row["drift"],
                "risk_score": row["risk_score"],
                "notes": row["notes"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def status(self, organization_id: str | None = None) -> dict[str, Any]:
        latest = next(iter(self.history(organization_id=organization_id, limit=1)), None)
        return {
            "organization_id": organization_id or "all",
            "running": self._worker.is_alive() if self._worker is not None else False,
            "latest_run": latest,
        }

    def _store_run(self, record: dict[str, Any]) -> None:
        with self.repository._connect() as conn:  # noqa: SLF001 - repository boundary shim
            conn.execute(
                """
                INSERT INTO assurance_scheduler_runs (
                    scheduler_run_id, organization_id, scheduled_at,
                    executed_at, status, trust_score, drift, risk_score,
                    notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["scheduler_run_id"],
                    record["organization_id"],
                    record["scheduled_at"],
                    record["executed_at"],
                    record["status"],
                    record["trust_score"],
                    record["drift"],
                    record["risk_score"],
                    record["notes"],
                    record["created_at"],
                ),
            )
            conn.commit()

    def _organizations(self) -> list[str]:
        with self.repository._connect() as conn:  # noqa: SLF001 - repository boundary shim
            rows = conn.execute("SELECT organization_id FROM organizations ORDER BY organization_id ASC").fetchall()
        orgs = [str(row["organization_id"]) for row in rows if row["organization_id"]]
        return orgs or [DEFAULT_ORGANIZATION_ID]


__all__ = ["AssuranceScheduler", "SchedulerRun"]
