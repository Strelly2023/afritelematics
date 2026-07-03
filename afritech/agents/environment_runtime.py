"""Environment-isolated runtime for non-authoritative AI decision agents.

Agents may be non-deterministic. Their outputs are persisted as proposals and
must pass a deterministic policy gate before any downstream executor may use
them. Production and staging never share state or admission policy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from hashlib import sha256
import json
import os
from pathlib import Path
import sqlite3
from types import MappingProxyType
from typing import Any, Callable, Mapping, Protocol
from uuid import uuid4


ENVIRONMENTS = frozenset({"production", "staging"})
RISK_LEVELS = frozenset({"low", "medium", "high", "critical"})
ADMISSION_STATUSES = frozenset({"admitted", "review_required", "rejected"})
RESERVED_DECISION_STATES = frozenset({"review_required", "admitted", "rejected"})
DEFAULT_ALLOWED_DECISION_STATES = frozenset({"review_required", "admitted", "rejected"})
DEFAULT_DECISION_TRANSITIONS: Mapping[str, frozenset[str]] = {
    "review_required": frozenset({"admitted", "rejected"}),
    "admitted": frozenset(),
    "rejected": frozenset(),
}


class AgentRuntimeViolation(RuntimeError):
    """Raised when an agent crosses an environment or authority boundary."""


class DecisionAgent(Protocol):
    agent_id: str

    def propose(self, context: Mapping[str, Any]) -> Mapping[str, Any]:
        """Return a non-authoritative proposal."""


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def _hash(value: Mapping[str, Any]) -> str:
    return sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def generate_proposal_id(
    proposal_payload: Mapping[str, Any],
    *,
    deterministic: bool = False,
    namespace: str | None = None,
) -> str:
    """Generate an invocation ID or a content-addressed retry ID.

    When deterministic is enabled, namespace narrows the hash scope so callers
    can keep production and staging retry identities separate.
    """
    if deterministic:
        material: dict[str, Any] = {"payload": _json_object(proposal_payload)}
        if namespace is not None:
            material["namespace"] = namespace
        return f"agent-proposal-{_hash(material)[:32]}"
    return f"agent-proposal-{uuid4().hex}"


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _json_object(value: Mapping[str, Any] | None) -> dict[str, Any]:
    payload = dict(value or {})
    try:
        encoded = _canonical_json(payload)
    except (TypeError, ValueError) as exc:
        raise AgentRuntimeViolation("proposal payload must be JSON serializable") from exc
    decoded = json.loads(encoded)
    if not isinstance(decoded, dict):
        raise AgentRuntimeViolation("proposal payload must be an object")
    return decoded


@dataclass(frozen=True)
class AgentProposal:
    proposal_id: str
    environment: str
    agent_id: str
    action: str
    rationale: str
    confidence: float
    risk: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    created_at: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )

    def canonical(self) -> dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "environment": self.environment,
            "agent_id": self.agent_id,
            "action": self.action,
            "rationale": self.rationale,
            "confidence": round(float(self.confidence), 6),
            "risk": self.risk,
            "payload": _json_object(self.payload),
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class AgentApproval:
    approved_by: str
    approval_ref: str

    def canonical(self) -> dict[str, str]:
        return {
            "approved_by": self.approved_by,
            "approval_ref": self.approval_ref,
        }


@dataclass(frozen=True)
class AdmissionDecision:
    proposal_id: str
    environment: str
    status: str
    executable: bool
    reason: str
    policy_version: str
    proposal_hash: str
    decision_hash: str
    approval: AgentApproval | None = None

    def canonical(self) -> dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "environment": self.environment,
            "status": self.status,
            "executable": self.executable,
            "reason": self.reason,
            "policy_version": self.policy_version,
            "proposal_hash": self.proposal_hash,
            "decision_hash": self.decision_hash,
            "approval": self.approval.canonical() if self.approval else None,
        }


@dataclass(frozen=True)
class EnvironmentAgentPolicy:
    environment: str
    allowed_actions: frozenset[str]
    minimum_confidence: float = 0.8
    policy_version: str = "afritech.agent-admission.v1"

    def __post_init__(self) -> None:
        if self.environment not in ENVIRONMENTS:
            raise AgentRuntimeViolation("unsupported agent environment")
        if not self.allowed_actions:
            raise AgentRuntimeViolation("allowed_actions cannot be empty")
        if not 0.0 <= self.minimum_confidence <= 1.0:
            raise AgentRuntimeViolation("minimum_confidence must be between 0 and 1")

    def evaluate(
        self,
        proposal: AgentProposal,
        *,
        approval: AgentApproval | None = None,
    ) -> AdmissionDecision:
        self._validate_proposal(proposal)
        proposal_hash = _hash(proposal.canonical())

        if proposal.action not in self.allowed_actions:
            return self._decision(
                proposal,
                proposal_hash,
                status="rejected",
                executable=False,
                reason="action_not_allowed",
                approval=approval,
            )
        if proposal.risk in {"high", "critical"}:
            return self._decision(
                proposal,
                proposal_hash,
                status="rejected",
                executable=False,
                reason="risk_exceeds_environment_policy",
                approval=approval,
            )
        if proposal.confidence < self.minimum_confidence:
            return self._decision(
                proposal,
                proposal_hash,
                status="review_required",
                executable=False,
                reason="confidence_below_threshold",
                approval=approval,
            )

        if self.environment == "production":
            if approval is None:
                return self._decision(
                    proposal,
                    proposal_hash,
                    status="review_required",
                    executable=False,
                    reason="production_approval_required",
                )
            if not approval.approved_by.strip() or not approval.approval_ref.strip():
                raise AgentRuntimeViolation("production approval identity and reference are required")

        return self._decision(
            proposal,
            proposal_hash,
            status="admitted",
            executable=True,
            reason=(
                "production_approval_validated"
                if self.environment == "production"
                else "staging_low_risk_auto_admission"
            ),
            approval=approval,
        )

    def _validate_proposal(self, proposal: AgentProposal) -> None:
        if proposal.environment != self.environment:
            raise AgentRuntimeViolation("cross_environment_proposal_rejected")
        if not proposal.proposal_id.strip() or not proposal.agent_id.strip():
            raise AgentRuntimeViolation("proposal and agent identifiers are required")
        if not proposal.action.strip() or not proposal.rationale.strip():
            raise AgentRuntimeViolation("proposal action and rationale are required")
        if proposal.risk not in RISK_LEVELS:
            raise AgentRuntimeViolation("unsupported proposal risk")
        if not 0.0 <= float(proposal.confidence) <= 1.0:
            raise AgentRuntimeViolation("proposal confidence must be between 0 and 1")
        _json_object(proposal.payload)

    def _decision(
        self,
        proposal: AgentProposal,
        proposal_hash: str,
        *,
        status: str,
        executable: bool,
        reason: str,
        approval: AgentApproval | None = None,
    ) -> AdmissionDecision:
        if status not in ADMISSION_STATUSES:
            raise AgentRuntimeViolation("unsupported admission status")
        decision_material = {
            "proposal_id": proposal.proposal_id,
            "environment": self.environment,
            "status": status,
            "executable": executable,
            "reason": reason,
            "policy_version": self.policy_version,
            "proposal_hash": proposal_hash,
            "approval": approval.canonical() if approval else None,
        }
        return AdmissionDecision(
            proposal_id=proposal.proposal_id,
            environment=self.environment,
            status=status,
            executable=executable,
            reason=reason,
            policy_version=self.policy_version,
            proposal_hash=proposal_hash,
            decision_hash=_hash(decision_material),
            approval=approval,
        )


@dataclass(frozen=True)
class DecisionTransitionPolicy:
    """Configurable workflow policy applied before ledger append."""

    environment: str
    allowed_states: frozenset[str] | None = None
    transitions: Mapping[str, frozenset[str]] = field(
        default_factory=lambda: dict(DEFAULT_DECISION_TRANSITIONS)
    )

    def __post_init__(self) -> None:
        if self.environment not in ENVIRONMENTS:
            raise AgentRuntimeViolation("unsupported agent environment")
        normalized = {
            str(source): frozenset(str(target) for target in targets)
            for source, targets in self.transitions.items()
        }
        if self.allowed_states is None:
            normalized_states = frozenset(DEFAULT_ALLOWED_DECISION_STATES)
        else:
            normalized_states = frozenset(
                str(state) for state in self.allowed_states if str(state).strip()
            )
            if len(normalized_states) != len(self.allowed_states) or not normalized_states:
                raise AgentRuntimeViolation("unsupported decision state")
        for source, targets in normalized.items():
            if not str(source).strip():
                raise AgentRuntimeViolation("unsupported transition source")
            if any(not str(target).strip() for target in targets):
                raise AgentRuntimeViolation("unsupported transition target")
            if source not in normalized_states:
                raise AgentRuntimeViolation(
                    f"transition_state_not_registered:{source}"
                )
            for target in targets:
                if target not in normalized_states:
                    raise AgentRuntimeViolation(
                        f"transition_state_not_registered:{target}"
                    )
        object.__setattr__(self, "allowed_states", normalized_states)
        object.__setattr__(
            self,
            "transitions",
            MappingProxyType(normalized),
        )

    def validate(
        self,
        previous: Mapping[str, Any],
        current: Mapping[str, Any],
    ) -> None:
        previous_environment = str(previous.get("environment", ""))
        current_environment = str(current.get("environment", ""))
        if (
            previous_environment != current_environment
            or current_environment != self.environment
        ):
            raise AgentRuntimeViolation(
                "cross_environment_decision_transition"
            )

        previous_status = str(previous.get("status", ""))
        current_status = str(current.get("status", ""))
        allowed = self.transitions.get(previous_status)
        if allowed is None or current_status not in allowed:
            raise AgentRuntimeViolation("invalid_decision_transition")

        if current_status == "admitted" and self.environment == "production":
            approval = current.get("approval")
            if (
                current.get("executable") is not True
                or not isinstance(approval, Mapping)
                or not str(approval.get("approved_by", "")).strip()
                or not str(approval.get("approval_ref", "")).strip()
            ):
                raise AgentRuntimeViolation("invalid_decision_transition")


class AgentDecisionStore:
    """Append-only SQLite ledger scoped to exactly one environment."""

    def __init__(
        self,
        path: str | Path,
        *,
        environment: str,
        transition_policy: DecisionTransitionPolicy | None = None,
    ) -> None:
        if environment not in ENVIRONMENTS:
            raise AgentRuntimeViolation("unsupported agent environment")
        self.path = Path(path)
        self.environment = environment
        self.transition_policy = transition_policy or DecisionTransitionPolicy(
            environment=environment
        )
        if self.transition_policy.environment != environment:
            raise AgentRuntimeViolation("store transition policy environment mismatch")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("BEGIN IMMEDIATE")
            try:
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS agent_proposals (
                        proposal_id TEXT PRIMARY KEY,
                        environment TEXT NOT NULL,
                        proposal_json TEXT NOT NULL,
                        proposal_hash TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    )
                    """
                )
                table = connection.execute(
                    """
                    SELECT sql
                    FROM sqlite_master
                    WHERE type = 'table' AND name = 'agent_decisions'
                    """
                ).fetchone()
                if table is None:
                    self._create_decisions_table(connection)
                elif self._legacy_decisions_schema(str(table["sql"])):
                    self._migrate_decisions_table(connection)
                else:
                    self._ensure_decisions_indexes(connection)
            except Exception:
                connection.rollback()
                raise
            else:
                connection.commit()

    @staticmethod
    def _create_decisions_table(connection: sqlite3.Connection) -> None:
        connection.execute(
            """
            CREATE TABLE agent_decisions (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                proposal_id TEXT NOT NULL,
                environment TEXT NOT NULL,
                decision_hash TEXT NOT NULL UNIQUE,
                decision_json TEXT NOT NULL,
                previous_record_hash TEXT NOT NULL,
                record_hash TEXT NOT NULL UNIQUE,
                FOREIGN KEY(proposal_id) REFERENCES agent_proposals(proposal_id)
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX agent_decisions_env_proposal_sequence
                ON agent_decisions (environment, proposal_id, sequence)
            """
        )

    @staticmethod
    def _ensure_decisions_indexes(connection: sqlite3.Connection) -> None:
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS agent_decisions_env_proposal_sequence
                ON agent_decisions (environment, proposal_id, sequence)
            """
        )
        connection.execute("DROP INDEX IF EXISTS agent_decisions_proposal_sequence")

    @staticmethod
    def _legacy_decisions_schema(sql: str) -> bool:
        normalized = " ".join(sql.upper().split())
        return (
            "DECISION_HASH TEXT" not in normalized
            or "PROPOSAL_ID TEXT NOT NULL UNIQUE" in normalized
        )

    def _migrate_decisions_table(self, connection: sqlite3.Connection) -> None:
        rows = connection.execute(
            """
            SELECT sequence, proposal_id, environment, decision_json,
                   previous_record_hash, record_hash
            FROM agent_decisions
            ORDER BY sequence
            """
        ).fetchall()
        expected_rows = [self._legacy_decision_key(row) for row in rows]
        connection.execute(
            "ALTER TABLE agent_decisions RENAME TO agent_decisions_legacy"
        )
        self._create_decisions_table(connection)
        for row in rows:
            try:
                decision = json.loads(str(row["decision_json"]))
            except (TypeError, json.JSONDecodeError) as exc:
                raise AgentRuntimeViolation(
                    "legacy_decision_migration_failed:decision_json_invalid"
                ) from exc
            decision_hash = (
                str(decision.get("decision_hash", ""))
                if isinstance(decision, dict)
                else ""
            )
            if not decision_hash:
                raise AgentRuntimeViolation(
                    "legacy_decision_migration_failed:missing_hash"
                )
            connection.execute(
                """
                INSERT INTO agent_decisions (
                    sequence, proposal_id, environment, decision_hash,
                    decision_json, previous_record_hash, record_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(row["sequence"]),
                    str(row["proposal_id"]),
                    str(row["environment"]),
                    decision_hash,
                    str(row["decision_json"]),
                    str(row["previous_record_hash"]),
                    str(row["record_hash"]),
                ),
            )
        copied_rows = connection.execute(
            """
            SELECT sequence, proposal_id, environment, decision_hash,
                   previous_record_hash, record_hash
            FROM agent_decisions
            ORDER BY sequence
            """
        ).fetchall()
        copied = connection.execute(
            """
            SELECT
                COUNT(*) AS count,
                COUNT(DISTINCT decision_hash) AS distinct_decision_hashes
            FROM agent_decisions
            """
        ).fetchone()
        if (
            copied is None
            or int(copied["count"]) != len(expected_rows)
        ):
            raise AgentRuntimeViolation(
                "legacy_decision_migration_failed:count_mismatch"
            )

        copied_sequences = [int(row["sequence"]) for row in copied_rows]
        expected_sequences = [row[0] for row in expected_rows]
        if copied_sequences != expected_sequences:
            raise AgentRuntimeViolation(
                "legacy_decision_migration_failed:sequence_mismatch"
            )

        copied_decision_hashes = [str(row["decision_hash"]) for row in copied_rows]
        expected_decision_hashes = [row[3] for row in expected_rows]
        if copied_decision_hashes != expected_decision_hashes:
            raise AgentRuntimeViolation(
                "legacy_decision_migration_failed:decision_hash_mismatch"
            )

        copied_record_hashes = [str(row["record_hash"]) for row in copied_rows]
        expected_record_hashes = [row[5] for row in expected_rows]
        if copied_record_hashes != expected_record_hashes:
            raise AgentRuntimeViolation(
                "legacy_decision_migration_failed:record_hash_mismatch"
            )

        if [self._decision_key(row) for row in copied_rows] != [
            (
                sequence,
                proposal_id,
                environment,
                decision_hash,
                previous_record_hash,
                record_hash,
            )
            for sequence, proposal_id, environment, decision_hash, previous_record_hash, record_hash in expected_rows
        ]:
            raise AgentRuntimeViolation(
                "legacy_decision_migration_failed:row_content_mismatch"
            )
        connection.execute("DROP TABLE agent_decisions_legacy")

    @staticmethod
    def _legacy_decision_key(row: sqlite3.Row) -> tuple[Any, ...]:
        try:
            decision = json.loads(str(row["decision_json"]))
        except (TypeError, json.JSONDecodeError) as exc:
            raise AgentRuntimeViolation(
                "legacy_decision_migration_failed:decision_json_invalid"
            ) from exc
        if not isinstance(decision, dict):
            raise AgentRuntimeViolation(
                "legacy_decision_migration_failed:decision_json_invalid"
            )
        decision_hash = str(decision.get("decision_hash", ""))
        if not decision_hash:
            raise AgentRuntimeViolation(
                "legacy_decision_migration_failed:missing_hash"
            )
        return (
            int(row["sequence"]),
            str(row["proposal_id"]),
            str(row["environment"]),
            decision_hash,
            str(row["previous_record_hash"]),
            str(row["record_hash"]),
        )

    @staticmethod
    def _decision_key(row: sqlite3.Row) -> tuple[Any, ...]:
        return (
            int(row["sequence"]),
            str(row["proposal_id"]),
            str(row["environment"]),
            str(row["decision_hash"]),
            str(row["previous_record_hash"]),
            str(row["record_hash"]),
        )

    def save(self, proposal: AgentProposal, decision: AdmissionDecision) -> str:
        if proposal.environment != self.environment or decision.environment != self.environment:
            raise AgentRuntimeViolation("cross_environment_state_write_rejected")
        if proposal.proposal_id != decision.proposal_id:
            raise AgentRuntimeViolation("proposal decision identity mismatch")

        proposal_payload = proposal.canonical()
        decision_payload = decision.canonical()
        proposal_hash = _hash(proposal_payload)
        if decision.proposal_hash != proposal_hash:
            raise AgentRuntimeViolation("proposal hash mismatch")

        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                "SELECT proposal_hash FROM agent_proposals WHERE proposal_id = ?",
                (proposal.proposal_id,),
            ).fetchone()
            if existing is not None:
                if str(existing["proposal_hash"]) != proposal_hash:
                    raise AgentRuntimeViolation("proposal_id_conflict")
            else:
                connection.execute(
                    """
                    INSERT INTO agent_proposals (
                        proposal_id, environment, proposal_json,
                        proposal_hash, created_at
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        proposal.proposal_id,
                        self.environment,
                        _canonical_json(proposal_payload),
                        proposal_hash,
                        proposal.created_at,
                    ),
                )

            repeated = connection.execute(
                """
                SELECT decision_json, record_hash
                FROM agent_decisions
                WHERE proposal_id = ? AND decision_hash = ?
                """,
                (proposal.proposal_id, decision.decision_hash),
            ).fetchone()
            if repeated is not None:
                if str(repeated["decision_json"]) != _canonical_json(decision_payload):
                    raise AgentRuntimeViolation("decision_hash_conflict")
                return str(repeated["record_hash"])

            latest_for_proposal = connection.execute(
                """
                SELECT decision_json
                FROM agent_decisions
                WHERE proposal_id = ?
                ORDER BY sequence DESC
                LIMIT 1
                """,
                (proposal.proposal_id,),
            ).fetchone()
            if latest_for_proposal is not None:
                previous_decision = self._stored_decision(latest_for_proposal)
                if previous_decision.get("proposal_hash") != decision.proposal_hash:
                    raise AgentRuntimeViolation("proposal_chain_mismatch")
                self.transition_policy.validate(
                    previous_decision,
                    decision_payload,
                )

            previous = connection.execute(
                """
                SELECT record_hash
                FROM agent_decisions
                WHERE environment = ?
                ORDER BY sequence DESC
                LIMIT 1
                """,
                (self.environment,),
            ).fetchone()
            previous_hash = str(previous["record_hash"]) if previous else "GENESIS"
            record_hash = _hash(
                {
                    "environment": self.environment,
                    "proposal": proposal_payload,
                    "decision": decision_payload,
                    "previous_record_hash": previous_hash,
                }
            )
            connection.execute(
                """
                INSERT INTO agent_decisions (
                    proposal_id, environment, decision_hash, decision_json,
                    previous_record_hash, record_hash
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    proposal.proposal_id,
                    self.environment,
                    decision.decision_hash,
                    _canonical_json(decision_payload),
                    previous_hash,
                    record_hash,
                ),
            )
            return record_hash

    @staticmethod
    def _stored_decision(row: sqlite3.Row) -> dict[str, Any]:
        try:
            stored = json.loads(str(row["decision_json"]))
        except (TypeError, json.JSONDecodeError) as exc:
            raise AgentRuntimeViolation("stored_decision_invalid") from exc
        if not isinstance(stored, dict):
            raise AgentRuntimeViolation("stored_decision_invalid")
        return stored

    def decisions(self) -> tuple[dict[str, Any], ...]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT sequence, proposal_id, decision_json,
                       previous_record_hash, record_hash
                FROM agent_decisions
                WHERE environment = ?
                ORDER BY sequence
                """,
                (self.environment,),
            ).fetchall()
        return self._records(rows)

    @staticmethod
    def _records(rows: list[sqlite3.Row]) -> tuple[dict[str, Any], ...]:
        return tuple(
            {
                "sequence": int(row["sequence"]),
                "proposal_id": str(row["proposal_id"]),
                "decision": json.loads(str(row["decision_json"])),
                "previous_record_hash": str(row["previous_record_hash"]),
                "record_hash": str(row["record_hash"]),
            }
            for row in rows
        )

    def decisions_for_proposal(
        self,
        proposal_id: str,
    ) -> tuple[dict[str, Any], ...]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT sequence, proposal_id, decision_json,
                       previous_record_hash, record_hash
                FROM agent_decisions
                WHERE environment = ? AND proposal_id = ?
                ORDER BY sequence
                """,
                (self.environment, proposal_id),
            ).fetchall()
        return self._records(rows)


@dataclass
class EnvironmentAgentRuntime:
    environment: str
    policy: EnvironmentAgentPolicy
    store: AgentDecisionStore
    clock: Callable[[], datetime] = field(default=_utc_now, repr=False)

    def __post_init__(self) -> None:
        if self.policy.environment != self.environment:
            raise AgentRuntimeViolation("runtime policy environment mismatch")
        if self.store.environment != self.environment:
            raise AgentRuntimeViolation("runtime store environment mismatch")

    def run(
        self,
        agent: DecisionAgent,
        context: Mapping[str, Any],
        *,
        approval: AgentApproval | None = None,
    ) -> AdmissionDecision:
        raw = _json_object(agent.propose(_json_object(context)))
        proposal = AgentProposal(
            # A missing ID denotes a new inference event. Agents that need
            # retry idempotency must emit a stable proposal_id themselves.
            proposal_id=str(
                raw.get("proposal_id")
                or generate_proposal_id(raw)
            ),
            environment=str(raw.get("environment") or self.environment),
            agent_id=str(agent.agent_id),
            action=str(raw.get("action") or ""),
            rationale=str(raw.get("rationale") or ""),
            confidence=float(raw.get("confidence", 0.0)),
            risk=str(raw.get("risk") or ""),
            payload=_json_object(raw.get("payload") if isinstance(raw.get("payload"), Mapping) else {}),
            created_at=self.clock().astimezone(UTC).isoformat(),
        )
        decision = self.policy.evaluate(proposal, approval=approval)
        self.store.save(proposal, decision)
        return decision


def build_environment_agent_runtime(
    *,
    environment: str,
    state_path: str | Path,
    allowed_actions: frozenset[str],
    minimum_confidence: float = 0.8,
) -> EnvironmentAgentRuntime:
    return EnvironmentAgentRuntime(
        environment=environment,
        policy=EnvironmentAgentPolicy(
            environment=environment,
            allowed_actions=allowed_actions,
            minimum_confidence=minimum_confidence,
        ),
        store=AgentDecisionStore(state_path, environment=environment),
    )


def build_environment_agent_runtime_from_env(
    *,
    allowed_actions: frozenset[str],
) -> EnvironmentAgentRuntime:
    environment = os.environ.get("AFRITECH_RUNTIME_ENVIRONMENT", "").strip().lower()
    state_path = os.environ.get("AFRITECH_AGENT_STATE_PATH", "").strip()
    if not environment or not state_path:
        raise AgentRuntimeViolation(
            "AFRITECH_RUNTIME_ENVIRONMENT and AFRITECH_AGENT_STATE_PATH are required"
        )
    minimum_confidence = float(
        os.environ.get("AFRITECH_AGENT_MINIMUM_CONFIDENCE", "0.8")
    )
    return build_environment_agent_runtime(
        environment=environment,
        state_path=state_path,
        allowed_actions=allowed_actions,
        minimum_confidence=minimum_confidence,
    )


__all__ = [
    "AdmissionDecision",
    "AgentApproval",
    "AgentDecisionStore",
    "AgentProposal",
    "AgentRuntimeViolation",
    "DecisionAgent",
    "DecisionTransitionPolicy",
    "EnvironmentAgentPolicy",
    "EnvironmentAgentRuntime",
    "build_environment_agent_runtime",
    "build_environment_agent_runtime_from_env",
    "generate_proposal_id",
    "RESERVED_DECISION_STATES",
]
