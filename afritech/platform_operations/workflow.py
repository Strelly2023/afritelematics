"""Checkpointed workflow orchestration with deterministic recovery."""

from __future__ import annotations

from dataclasses import dataclass, replace
import json
from pathlib import Path
import sqlite3
from typing import Any, Mapping, Protocol


TERMINAL = {"COMPLETED", "FAILED", "COMPENSATED", "CANCELLED"}


@dataclass(frozen=True)
class WorkflowStep:
    id: str
    action: str
    compensation: str
    timeout_seconds: int = 300
    max_attempts: int = 3


@dataclass(frozen=True)
class WorkflowDefinition:
    workflow_id: str
    version: str
    steps: tuple[WorkflowStep, ...]


@dataclass(frozen=True)
class WorkflowInstance:
    instance_id: str
    definition_id: str
    definition_version: str
    tenant_id: str
    state: str
    step_index: int
    revision: int
    context: Mapping[str, Any]
    history: tuple[Mapping[str, Any], ...] = ()


class WorkflowStore(Protocol):
    def load(self, instance_id: str) -> WorkflowInstance | None: ...
    def save(self, instance: WorkflowInstance, *, expected_revision: int) -> None: ...


class InMemoryWorkflowStore:
    def __init__(self) -> None:
        self.instances: dict[str, WorkflowInstance] = {}

    def load(self, instance_id: str) -> WorkflowInstance | None:
        return self.instances.get(instance_id)

    def save(self, instance: WorkflowInstance, *, expected_revision: int) -> None:
        current = self.instances.get(instance.instance_id)
        actual = current.revision if current else 0
        if actual != expected_revision:
            raise RuntimeError("workflow_concurrency_conflict")
        self.instances[instance.instance_id] = instance


class SQLiteWorkflowStore:
    """Durable local store; production adapters can implement the same protocol."""

    def __init__(self, path: Path | str) -> None:
        self.path = str(path)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS novatech_workflow_instances (
                    instance_id TEXT PRIMARY KEY,
                    revision INTEGER NOT NULL,
                    payload TEXT NOT NULL
                )
                """
            )

    def load(self, instance_id: str) -> WorkflowInstance | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT payload
                FROM novatech_workflow_instances
                WHERE instance_id = ?
                """,
                (instance_id,),
            ).fetchone()
        if row is None:
            return None
        payload = json.loads(row[0])
        return WorkflowInstance(
            instance_id=payload["instance_id"],
            definition_id=payload["definition_id"],
            definition_version=payload["definition_version"],
            tenant_id=payload["tenant_id"],
            state=payload["state"],
            step_index=payload["step_index"],
            revision=payload["revision"],
            context=payload["context"],
            history=tuple(payload["history"]),
        )

    def save(self, instance: WorkflowInstance, *, expected_revision: int) -> None:
        payload = json.dumps(
            {
                "instance_id": instance.instance_id,
                "definition_id": instance.definition_id,
                "definition_version": instance.definition_version,
                "tenant_id": instance.tenant_id,
                "state": instance.state,
                "step_index": instance.step_index,
                "revision": instance.revision,
                "context": dict(instance.context),
                "history": list(instance.history),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        with self._connect() as connection:
            if expected_revision == 0:
                try:
                    connection.execute(
                        """
                        INSERT INTO novatech_workflow_instances
                            (instance_id, revision, payload)
                        VALUES (?, ?, ?)
                        """,
                        (instance.instance_id, instance.revision, payload),
                    )
                except sqlite3.IntegrityError as exc:
                    raise RuntimeError("workflow_concurrency_conflict") from exc
                return
            cursor = connection.execute(
                """
                UPDATE novatech_workflow_instances
                SET revision = ?, payload = ?
                WHERE instance_id = ? AND revision = ?
                """,
                (
                    instance.revision,
                    payload,
                    instance.instance_id,
                    expected_revision,
                ),
            )
            if cursor.rowcount != 1:
                raise RuntimeError("workflow_concurrency_conflict")

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)


class DurableWorkflowEngine:
    def __init__(self, store: WorkflowStore) -> None:
        self.store = store

    def start(
        self,
        definition: WorkflowDefinition,
        *,
        instance_id: str,
        tenant_id: str,
        context: Mapping[str, Any],
    ) -> WorkflowInstance:
        if not definition.steps:
            raise ValueError("workflow_steps_required")
        instance = WorkflowInstance(
            instance_id=instance_id,
            definition_id=definition.workflow_id,
            definition_version=definition.version,
            tenant_id=tenant_id,
            state="PENDING",
            step_index=0,
            revision=1,
            context=dict(context),
            history=({"event": "STARTED", "step_index": 0},),
        )
        self.store.save(instance, expected_revision=0)
        return instance

    def advance(
        self,
        definition: WorkflowDefinition,
        instance_id: str,
        *,
        step_result: Mapping[str, Any],
    ) -> WorkflowInstance:
        current = self._required(instance_id)
        if current.state in TERMINAL:
            return current
        if current.definition_id != definition.workflow_id:
            raise ValueError("workflow_definition_mismatch")
        failed = step_result.get("status") == "FAILED"
        next_index = current.step_index if failed else current.step_index + 1
        next_state = (
            "COMPENSATING"
            if failed
            else "COMPLETED"
            if next_index >= len(definition.steps)
            else "RUNNING"
        )
        updated = replace(
            current,
            state=next_state,
            step_index=next_index,
            revision=current.revision + 1,
            history=current.history
            + (
                {
                    "event": "STEP_FAILED" if failed else "STEP_COMPLETED",
                    "step_index": current.step_index,
                    "result": dict(step_result),
                },
            ),
        )
        self.store.save(updated, expected_revision=current.revision)
        return updated

    def compensate(self, instance_id: str) -> WorkflowInstance:
        current = self._required(instance_id)
        if current.state != "COMPENSATING":
            raise ValueError("workflow_not_compensating")
        updated = replace(
            current,
            state="COMPENSATED",
            revision=current.revision + 1,
            history=current.history + ({"event": "COMPENSATED"},),
        )
        self.store.save(updated, expected_revision=current.revision)
        return updated

    def recover(self, instance_id: str) -> WorkflowInstance:
        return self._required(instance_id)

    def _required(self, instance_id: str) -> WorkflowInstance:
        instance = self.store.load(instance_id)
        if instance is None:
            raise KeyError("workflow_instance_not_found")
        return instance
