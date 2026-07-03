"""Read-only blockchain anchor indexing and verification helpers.

The indexer keeps a deterministic in-process record of anchor publications so
the API, proof generator, and dashboard can all expose the same operational
surface without reinterpreting chain authority.
"""

from __future__ import annotations

import asyncio
import contextlib
from dataclasses import dataclass, field
import hashlib
import json
import os
import queue
from html import escape
from pathlib import Path
import threading
import time
from typing import Any, cast

from afritech.architecture.blockchain_anchor import (
    BlockchainAnchorPublication,
    build_chain_promotion_plan,
    get_chain_profile,
    list_chain_profiles,
    resolve_chain_ws_url,
)
from afritech.chain.contracts.architecture_anchor_abi import ARCHITECTURE_ANCHOR_ABI
from afritech.chain.contracts.architecture_anchor_v2_abi import ARCHITECTURE_ANCHOR_V2_ABI
from afritech.chain.contracts.contract_client import chain_health
from afritech.chain.contracts.deployment_config import PLACEHOLDER_CONTRACT_ADDRESSES
from afritech.chain.types import ChainReceipt


def _json_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _contract_explorer_url(profile_name: str | None, contract_address: str | None) -> str | None:
    if not contract_address:
        return None

    try:
        profile = get_chain_profile(profile_name or os.getenv("AFRITECH_CHAIN_MODE", "sepolia"))
    except Exception:
        return None

    base = profile.explorer_base_url.rstrip("/")
    if "/tx" in base:
        base = base.replace("/tx", "/address")
    return f"{base}/{contract_address}"


def _abi_fingerprint() -> str:
    return _json_hash(ARCHITECTURE_ANCHOR_ABI)


def _abi_v2_fingerprint() -> str:
    return _json_hash(ARCHITECTURE_ANCHOR_V2_ABI)


def _coerce_receipt(payload: ChainReceipt | dict[str, Any]) -> dict[str, Any]:
    if isinstance(payload, ChainReceipt):
        return payload.canonical_dict()
    return dict(payload)


def _hex_value(value: Any) -> str:
    if value is None:
        return ""
    hex_method = getattr(value, "hex", None)
    if callable(hex_method):
        return str(hex_method())
    return str(value)


def _bytes32_context(value: Any) -> str:
    raw_hex = _hex_value(value).removeprefix("0x")
    if not raw_hex:
        return ""
    try:
        return bytes.fromhex(raw_hex).rstrip(b"\x00").decode("utf-8", errors="replace")
    except ValueError:
        return str(value)


def _event_args(event: Any) -> Any:
    if isinstance(event, dict):
        return event.get("args") or {}
    return getattr(event, "args", {})


def _event_value(event: Any, key: str, default: Any = None) -> Any:
    if isinstance(event, dict):
        return event.get(key, default)
    return getattr(event, key, default)


def _event_arg(args: Any, key: str, default: Any = None) -> Any:
    if isinstance(args, dict):
        return args.get(key, default)
    return getattr(args, key, default)


def _int_or_default(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _entry_key_from_parts(anchor_id: str, network: str, transaction_hash: str, publication_id: str) -> str:
    suffix = transaction_hash or publication_id or "unpublished"
    return f"{anchor_id}::{network}::{suffix}"


def _entry_key(entry: "AnchorIndexEntry") -> str:
    return _entry_key_from_parts(
        entry.anchor_id,
        entry.network,
        entry.transaction_hash,
        entry.publication_id,
    )


EVIDENCE_CONSISTENCY_INVARIANTS: tuple[dict[str, Any], ...] = (
    {
        "id": "RECONCILIATION-001",
        "name": "Proof hash grouping",
        "rule": "observations_with_the_same_proof_hash_are_reconciled_as_one_evidence_set",
        "failure_status": "DIVERGENT",
    },
    {
        "id": "RECONCILIATION-002",
        "name": "Anchor identity consistency",
        "rule": "a_reconciled_evidence_set_must_have_one_anchor_id",
        "failure_status": "DIVERGENT",
    },
    {
        "id": "RECONCILIATION-003",
        "name": "Contract consistency",
        "rule": "a_reconciled_evidence_set_must_not_mix_contract_addresses",
        "failure_status": "DIVERGENT",
    },
    {
        "id": "RECONCILIATION-004",
        "name": "Network coverage",
        "rule": "mainnet_promotion_requires_required_pre_mainnet_network_observations",
        "failure_status": "PARTIAL",
    },
    {
        "id": "RECONCILIATION-005",
        "name": "Read-only evidence",
        "rule": "reconciliation_must_not_mutate_chain_state_or_claim_truth_authority",
        "failure_status": "POLICY_VIOLATION",
    },
)


CONFLICT_RESOLUTION_STRATEGIES: dict[str, dict[str, Any]] = {
    "RECONCILED": {
        "resolution_state": "NO_ACTION_REQUIRED",
        "operator_action": "continue_observation_and_allow_promotion_gates_to_evaluate",
        "allowed_actions": ["promote_if_required_networks_are_present", "publish_verification_packet"],
        "forbidden_actions": ["rewrite_observations", "treat_chain_as_truth"],
        "mainnet_blocking": False,
    },
    "PARTIAL": {
        "resolution_state": "AWAIT_REQUIRED_OBSERVATIONS",
        "operator_action": "continue_websocket_observation_and_backfill_missing_required_networks",
        "allowed_actions": ["backfill_logs", "continue_streaming", "publish_non_mainnet_evidence"],
        "forbidden_actions": ["promote_to_mainnet", "delete_partial_observation"],
        "mainnet_blocking": True,
    },
    "DIVERGENT": {
        "resolution_state": "GOVERNANCE_REVIEW_REQUIRED",
        "operator_action": "freeze_mainnet_promotion_open_governance_review_and_publish_resolution_adr",
        "allowed_actions": ["open_resolution_adr", "isolate_conflicting_observations", "republish_superseding_anchor_after_governance"],
        "forbidden_actions": ["promote_to_mainnet", "overwrite_conflict", "silently_pick_winner"],
        "mainnet_blocking": True,
    },
    "SINGLE_NETWORK": {
        "resolution_state": "INSUFFICIENT_DISTRIBUTED_EVIDENCE",
        "operator_action": "observe_required_pre_mainnet_networks_before_mainnet_promotion",
        "allowed_actions": ["publish_to_required_test_network", "continue_streaming"],
        "forbidden_actions": ["promote_to_mainnet"],
        "mainnet_blocking": True,
    },
}


EVIDENCE_LIFECYCLE_STATES: tuple[dict[str, Any], ...] = (
    {
        "id": "GOVERNED_DECISION",
        "authority": "governance",
        "description": "An ADR, RULE, or BIND defines what may be anchored.",
    },
    {
        "id": "PROOF_GENERATED",
        "authority": "replay/proof",
        "description": "A deterministic architecture proof and proof hash are generated.",
    },
    {
        "id": "PUBLISHED",
        "authority": "publication_evidence",
        "description": "The proof hash is submitted to a configured blockchain network.",
    },
    {
        "id": "OBSERVED",
        "authority": "observation",
        "description": "Read-only subscribers observe contract events from one or more networks.",
    },
    {
        "id": "NORMALIZED",
        "authority": "indexing",
        "description": "Observed events are converted into deterministic anchor index rows.",
    },
    {
        "id": "RECONCILED",
        "authority": "consistency_analysis",
        "description": "Normalized observations are grouped by proof hash and checked across networks.",
    },
    {
        "id": "POLICY_EVALUATED",
        "authority": "governance_policy",
        "description": "Evidence invariants and conflict strategies are applied without mutating evidence.",
    },
    {
        "id": "PROMOTION_GATED",
        "authority": "operational_control",
        "description": "Mainnet progression is approved or blocked from reconciliation and stream state.",
    },
    {
        "id": "PUBLICLY_VERIFIABLE",
        "authority": "public_visibility",
        "description": "Explorer, API, contract metadata, and replay surfaces expose evidence for verification.",
    },
)


EVIDENCE_OPERATIONAL_TRANSITIONS: tuple[dict[str, Any], ...] = (
    {
        "id": "ADR_TO_PROOF",
        "from": "GOVERNED_DECISION",
        "to": "PROOF_GENERATED",
        "guard": "adr_rule_bind_present_and_hashable",
        "input": "governance_artifact",
        "output": "deterministic_proof_hash",
    },
    {
        "id": "PROOF_TO_PUBLICATION",
        "from": "PROOF_GENERATED",
        "to": "PUBLISHED",
        "guard": "publication_profile_configured",
        "input": "proof_hash",
        "output": "transaction_or_contract_receipt",
    },
    {
        "id": "PUBLICATION_TO_OBSERVATION",
        "from": "PUBLISHED",
        "to": "OBSERVED",
        "guard": "read_only_event_subscriber_enabled",
        "input": "contract_event_log",
        "output": "observed_anchor_event",
    },
    {
        "id": "OBSERVATION_TO_NORMALIZATION",
        "from": "OBSERVED",
        "to": "NORMALIZED",
        "guard": "event_matches_architecture_anchor_schema",
        "input": "observed_anchor_event",
        "output": "anchor_index_entry",
    },
    {
        "id": "NORMALIZATION_TO_RECONCILIATION",
        "from": "NORMALIZED",
        "to": "RECONCILED",
        "guard": "entries_grouped_by_proof_hash",
        "input": "anchor_index_entries",
        "output": "reconciliation_report",
    },
    {
        "id": "RECONCILIATION_TO_POLICY",
        "from": "RECONCILED",
        "to": "POLICY_EVALUATED",
        "guard": "reconciliation_invariants_available",
        "input": "reconciliation_report",
        "output": "resolution_strategy",
    },
    {
        "id": "POLICY_TO_PROMOTION_GATE",
        "from": "POLICY_EVALUATED",
        "to": "PROMOTION_GATED",
        "guard": "no_divergence_required_networks_present_websocket_primary",
        "input": "policy_evaluation",
        "output": "mainnet_gate_decision",
    },
    {
        "id": "GATE_TO_PUBLIC_VERIFICATION",
        "from": "PROMOTION_GATED",
        "to": "PUBLICLY_VERIFIABLE",
        "guard": "public_surfaces_available",
        "input": "evidence_packet",
        "output": "public_verification_surface",
    },
)


GOVERNED_EVIDENCE_PROTOCOL_VERSION = "1.0.0"

GOVERNED_EVIDENCE_GOVERNANCE_ARTIFACTS: tuple[dict[str, str], ...] = (
    {
        "id": "ADR-0047",
        "type": "ADR",
        "path": "afritech/governance/adr/ADR-0047-governed-evidence-operating-protocol.yaml",
    },
    {
        "id": "RULE-067",
        "type": "RULE",
        "path": "afritech/governance/rules/RULE-067-governed-evidence-operating-protocol.yaml",
    },
    {
        "id": "BIND-045",
        "type": "BIND",
        "path": "afritech/governance/bindings/BIND-045-governed-evidence-operating-protocol.yaml",
    },
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _file_sha256(relative_path: str) -> str | None:
    path = _repo_root() / relative_path
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


class AnchorIndexBackendError(RuntimeError):
    """Raised when anchor index persistence fails."""


class AnchorIndexBackend:
    """Backend contract for anchor index persistence."""

    backend_name = "memory"

    def load_rows(self) -> list[dict[str, Any]]:
        return []

    def append_row(self, row: dict[str, Any]) -> None:
        raise NotImplementedError

    def replace_rows(self, rows: list[dict[str, Any]]) -> None:
        raise NotImplementedError

    def describe(self) -> dict[str, Any]:
        return {"backend": self.backend_name}


class InMemoryAnchorIndexBackend(AnchorIndexBackend):
    backend_name = "memory"

    def __init__(self, rows: list[dict[str, Any]] | None = None) -> None:
        self._rows = [dict(row) for row in rows or []]

    def load_rows(self) -> list[dict[str, Any]]:
        return [dict(row) for row in self._rows]

    def append_row(self, row: dict[str, Any]) -> None:
        self._rows.append(dict(row))

    def replace_rows(self, rows: list[dict[str, Any]]) -> None:
        self._rows = [dict(row) for row in rows]

    def describe(self) -> dict[str, Any]:
        return {"backend": self.backend_name, "rows": len(self._rows)}


class JsonFileAnchorIndexBackend(AnchorIndexBackend):
    backend_name = "file"

    def __init__(self, path: str) -> None:
        from pathlib import Path

        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

    def load_rows(self) -> list[dict[str, Any]]:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return []
        except json.JSONDecodeError as exc:
            raise AnchorIndexBackendError(f"invalid anchor index file: {exc}") from exc
        if not isinstance(payload, list):
            raise AnchorIndexBackendError("anchor index file must contain a list")
        return [dict(row) for row in payload if isinstance(row, dict)]

    def append_row(self, row: dict[str, Any]) -> None:
        rows = self.load_rows()
        rows.append(dict(row))
        self.replace_rows(rows)

    def replace_rows(self, rows: list[dict[str, Any]]) -> None:
        tmp_path = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp_path.write_text(
            json.dumps(rows, sort_keys=True, indent=2, default=str),
            encoding="utf-8",
        )
        tmp_path.replace(self.path)

    def describe(self) -> dict[str, Any]:
        return {"backend": self.backend_name, "path": str(self.path)}


class RedisAnchorIndexBackend(AnchorIndexBackend):
    backend_name = "redis"

    def __init__(self, url: str, key: str | None = None) -> None:
        try:
            import redis  # type: ignore[import-not-found]
        except ModuleNotFoundError as exc:
            raise AnchorIndexBackendError("redis is required for Redis anchor index backend") from exc

        self.redis = cast(Any, redis.Redis.from_url(url))
        self.key = key or "afritech:chain:anchor:index"

    def load_rows(self) -> list[dict[str, Any]]:
        rows = self.redis.lrange(self.key, 0, -1)
        decoded: list[dict[str, Any]] = []
        for row in rows:
            payload = json.loads(row.decode("utf-8"))
            if isinstance(payload, dict):
                decoded.append(payload)
        return decoded

    def append_row(self, row: dict[str, Any]) -> None:
        self.redis.rpush(self.key, json.dumps(row, sort_keys=True, default=str))

    def replace_rows(self, rows: list[dict[str, Any]]) -> None:
        pipe = self.redis.pipeline()
        pipe.delete(self.key)
        if rows:
            pipe.rpush(self.key, *[json.dumps(row, sort_keys=True, default=str) for row in rows])
        pipe.execute()

    def describe(self) -> dict[str, Any]:
        return {"backend": self.backend_name, "key": self.key}


class PostgresAnchorIndexBackend(AnchorIndexBackend):
    backend_name = "postgres"

    def __init__(self, dsn: str, table_name: str | None = None, auto_create: bool = False) -> None:
        try:
            import psycopg
        except ModuleNotFoundError as exc:
            raise AnchorIndexBackendError("psycopg is required for Postgres anchor index backend") from exc

        self._psycopg: Any = psycopg
        self.dsn = dsn
        self.table_name = table_name or "afritech_anchor_index"
        self.auto_create = auto_create
        if auto_create:
            self._ensure_schema()

    def _connect(self):
        return self._psycopg.connect(self.dsn)

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur = cast(Any, cur)
                cur.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {self.table_name} (
                        anchor_id text PRIMARY KEY,
                        sequence integer NOT NULL,
                        payload jsonb NOT NULL
                    )
                    """
                )
                conn.commit()

    def load_rows(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur = cast(Any, cur)
                cur.execute(
                    f"SELECT payload FROM {self.table_name} ORDER BY sequence ASC"
                )
                rows = cur.fetchall()
        decoded: list[dict[str, Any]] = []
        for (payload,) in rows:
            if isinstance(payload, str):
                decoded.append(json.loads(payload))
            else:
                decoded.append(dict(payload))
        return decoded

    def append_row(self, row: dict[str, Any]) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur = cast(Any, cur)
                cur.execute(
                    f"INSERT INTO {self.table_name} (anchor_id, sequence, payload) VALUES (%s, %s, %s)",
                    (row.get("anchor_id"), row.get("sequence"), json.dumps(row, sort_keys=True, default=str)),
                )
                conn.commit()

    def replace_rows(self, rows: list[dict[str, Any]]) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur = cast(Any, cur)
                cur.execute(f"DELETE FROM {self.table_name}")
                for row in rows:
                    cur.execute(
                        f"INSERT INTO {self.table_name} (anchor_id, sequence, payload) VALUES (%s, %s, %s)",
                        (row.get("anchor_id"), row.get("sequence"), json.dumps(row, sort_keys=True, default=str)),
                    )
                conn.commit()

    def describe(self) -> dict[str, Any]:
        return {"backend": self.backend_name, "table": self.table_name}


def _build_anchor_backend() -> AnchorIndexBackend:
    backend_name = os.getenv("AFRITECH_CHAIN_INDEX_BACKEND", "memory").strip().lower()
    if backend_name == "file":
        path = os.getenv("AFRITECH_CHAIN_INDEX_FILE", str(Path.home() / ".afritech" / "anchor-index.json"))
        return JsonFileAnchorIndexBackend(path)
    if backend_name == "redis":
        redis_url = os.getenv("AFRITECH_CHAIN_INDEX_REDIS_URL")
        if not redis_url:
            raise AnchorIndexBackendError("AFRITECH_CHAIN_INDEX_REDIS_URL is required for redis backend")
        return RedisAnchorIndexBackend(redis_url, os.getenv("AFRITECH_CHAIN_INDEX_REDIS_KEY"))
    if backend_name == "postgres":
        dsn = os.getenv("AFRITECH_CHAIN_INDEX_DATABASE_URL") or os.getenv("AFRITECH_DATABASE_URL")
        if not dsn:
            raise AnchorIndexBackendError("AFRITECH_CHAIN_INDEX_DATABASE_URL or AFRITECH_DATABASE_URL is required for postgres backend")
        return PostgresAnchorIndexBackend(
            dsn,
            table_name=os.getenv("AFRITECH_CHAIN_INDEX_TABLE", "afritech_anchor_index"),
            auto_create=os.getenv("AFRITECH_CHAIN_INDEX_AUTO_CREATE", "false").lower() == "true",
        )
    return InMemoryAnchorIndexBackend()


@dataclass(frozen=True)
class AnchorIndexEntry:
    anchor_id: str
    publication_id: str
    proof_hash: str | None
    network: str
    chain_id: int | None
    chain_name: str | None
    contract_address: str | None
    transaction_hash: str
    block_number: int | None
    explorer_url: str | None
    anchor_mode: str
    status: str
    source: str
    sequence: int
    contract_explorer_url: str | None = None
    etherscan_verification_stage: str = "READY_FOR_SUBMISSION"
    authority_boundary: str = "anchor_index_is_read_only"
    meta: dict[str, Any] = field(default_factory=dict)

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "schema": "afritech.blockchain_anchor_index_entry.v1",
            "anchor_id": self.anchor_id,
            "publication_id": self.publication_id,
            "proof_hash": self.proof_hash,
            "network": self.network,
            "chain_id": self.chain_id,
            "chain_name": self.chain_name,
            "contract_address": self.contract_address,
            "transaction_hash": self.transaction_hash,
            "block_number": self.block_number,
            "explorer_url": self.explorer_url,
            "anchor_mode": self.anchor_mode,
            "status": self.status,
            "source": self.source,
            "sequence": self.sequence,
            "contract_explorer_url": self.contract_explorer_url,
            "etherscan_verification_stage": self.etherscan_verification_stage,
            "authority_boundary": self.authority_boundary,
            "meta": self.meta,
        }


def _entry_from_row(row: dict[str, Any]) -> AnchorIndexEntry:
    return AnchorIndexEntry(
        anchor_id=str(row["anchor_id"]),
        publication_id=str(row.get("publication_id") or ""),
        proof_hash=row.get("proof_hash"),
        network=str(row.get("network") or "unknown"),
        chain_id=int(row["chain_id"]) if row.get("chain_id") is not None else None,
        chain_name=str(row["chain_name"]) if row.get("chain_name") is not None else None,
        contract_address=str(row["contract_address"]) if row.get("contract_address") is not None else None,
        transaction_hash=str(row.get("transaction_hash") or ""),
        block_number=int(row["block_number"]) if row.get("block_number") is not None else None,
        explorer_url=str(row["explorer_url"]) if row.get("explorer_url") is not None else None,
        anchor_mode=str(row.get("anchor_mode") or "unknown"),
        status=str(row.get("status") or "unknown"),
        source=str(row.get("source") or "unknown"),
        sequence=int(row.get("sequence") or 0),
        contract_explorer_url=str(row["contract_explorer_url"]) if row.get("contract_explorer_url") is not None else None,
        etherscan_verification_stage=str(row.get("etherscan_verification_stage") or "READY_FOR_SUBMISSION"),
        authority_boundary=str(row.get("authority_boundary") or "anchor_index_is_read_only"),
        meta=dict(row.get("meta") or {}),
    )


def _stream_event_from_entry(
    entry: AnchorIndexEntry,
    *,
    event_type: str = "ANCHOR_INDEX_UPDATED",
    source: str | None = None,
) -> dict[str, Any]:
    payload = entry.canonical_dict()
    return {
        "classification": "BLOCKCHAIN_ANCHOR_STREAM_EVENT",
        "status": "READY",
        "event_type": event_type,
        "source": source or entry.source,
        "anchor_id": entry.anchor_id,
        "publication_id": entry.publication_id,
        "network": entry.network,
        "chain_id": entry.chain_id,
        "chain_name": entry.chain_name,
        "transaction_hash": entry.transaction_hash,
        "block_number": entry.block_number,
        "proof_hash": entry.proof_hash,
        "anchor_mode": entry.anchor_mode,
        "index_record": payload,
        "authority_boundary": "event_subscription_is_read_only_and_indexing_only",
    }


class AnchorStreamHub:
    """Broadcasts anchor index updates to websocket clients."""

    def __init__(self) -> None:
        self._clients: list[Any] = []
        self._queue: queue.Queue[dict[str, Any]] = queue.Queue()
        self._recent_events: list[dict[str, Any]] = []
        self._recent_limit = 100
        self._sequence = 0
        self._dispatch_task: asyncio.Task[None] | None = None
        self._stop_requested = False
        self._lock = threading.Lock()

    def subscribe(self, client: Any) -> None:
        with self._lock:
            if client not in self._clients:
                self._clients.append(client)

    def unsubscribe(self, client: Any) -> None:
        with self._lock:
            if client in self._clients:
                self._clients.remove(client)

    def publish(self, event: dict[str, Any]) -> None:
        with self._lock:
            self._sequence += 1
            sequence = self._sequence
        enriched = {
            "stream_sequence": sequence,
            "stream_event_id": f"anchor-stream-{sequence:012d}",
            "emitted_at_unix": int(time.time()),
            **dict(event),
        }
        self._queue.put(enriched)

    def recent_events(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._lock:
            events = list(self._recent_events[-max(1, limit):])
        return [dict(event) for event in events]

    def replay_after(self, after_sequence: int = 0, limit: int = 50) -> list[dict[str, Any]]:
        with self._lock:
            events = [
                dict(event)
                for event in self._recent_events
                if int(event.get("stream_sequence") or 0) > after_sequence
            ]
        return events[: max(1, min(limit, self._recent_limit))]

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            clients = len(self._clients)
            recent = [dict(event) for event in self._recent_events[-10:]]
            latest_sequence = self._sequence
        return {
            "classification": "BLOCKCHAIN_ANCHOR_STREAM_STATUS",
            "status": "READY",
            "transport": "websocket",
            "enabled": True,
            "connected_clients": clients,
            "queued_events": self._queue.qsize(),
            "latest_sequence": latest_sequence,
            "recent_events": recent,
            "authority_boundary": "event_subscription_is_read_only_and_indexing_only",
        }

    async def start(self) -> None:
        if self._dispatch_task is not None and not self._dispatch_task.done():
            return
        self._stop_requested = False
        self._dispatch_task = asyncio.create_task(self._dispatch_loop())

    async def stop(self) -> None:
        self._stop_requested = True
        if self._dispatch_task is not None:
            self._dispatch_task.cancel()
            with contextlib.suppress(Exception):
                await self._dispatch_task
        self._dispatch_task = None

    async def _dispatch_loop(self) -> None:
        while not self._stop_requested:
            try:
                event = await asyncio.to_thread(self._queue.get, True, 1.0)
            except queue.Empty:
                continue
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(0.5)
                continue

            with self._lock:
                self._recent_events.append(dict(event))
                self._recent_events = self._recent_events[-self._recent_limit :]
                clients = tuple(self._clients)

            for client in clients:
                try:
                    await client.send_json(event)
                except Exception:
                    self.unsubscribe(client)


ANCHOR_STREAM_HUB = AnchorStreamHub()


class AnchorIndexStore:
    """In-memory deterministic anchor index used by API and dashboard surfaces."""

    def __init__(self, backend: AnchorIndexBackend | None = None) -> None:
        self.backend = backend or InMemoryAnchorIndexBackend()
        self._entries: dict[str, AnchorIndexEntry] = {}
        self._order: list[str] = []
        self.refresh()

    def refresh(self) -> None:
        self._entries.clear()
        self._order.clear()
        for row in self.backend.load_rows():
            try:
                entry = _entry_from_row(row)
            except Exception:
                continue
            key = _entry_key(entry)
            self._entries[key] = entry
            self._order.append(key)

    def remember(self, entry: AnchorIndexEntry) -> AnchorIndexEntry:
        key = _entry_key(entry)
        is_new = key not in self._entries
        if is_new:
            self._order.append(key)
        self._entries[key] = entry
        if is_new:
            self.backend.append_row(entry.canonical_dict())
        else:
            self.backend.replace_rows([self._entries[entry_key].canonical_dict() for entry_key in self._order])
        try:
            ANCHOR_STREAM_HUB.publish(
                _stream_event_from_entry(
                    entry,
                    event_type="ANCHOR_INDEX_CREATED" if is_new else "ANCHOR_INDEX_UPDATED",
                    source="anchor_index_store",
                )
            )
        except Exception:
            pass
        return entry

    def load(self, anchor_id: str) -> AnchorIndexEntry:
        if anchor_id in self._entries:
            return self._entries[anchor_id]
        matches = [self._entries[entry_key] for entry_key in self._order if self._entries[entry_key].anchor_id == anchor_id]
        if not matches:
            raise KeyError(anchor_id)
        return matches[-1]

    def find_by_anchor_id(self, anchor_id: str) -> tuple[AnchorIndexEntry, ...]:
        return tuple(
            self._entries[entry_key]
            for entry_key in self._order
            if self._entries[entry_key].anchor_id == anchor_id
        )

    def list_entries(self) -> tuple[AnchorIndexEntry, ...]:
        return tuple(self._entries[entry_key] for entry_key in self._order)

    def latest(self) -> AnchorIndexEntry | None:
        if not self._order:
            return None
        return self._entries[self._order[-1]]

    def clear(self) -> None:
        self._entries.clear()
        self._order.clear()
        self.backend.replace_rows([])

    def describe(self) -> dict[str, Any]:
        return self.backend.describe()


ANCHOR_INDEX_STORE = AnchorIndexStore(_build_anchor_backend())


def _build_entry(
    *,
    anchor_id: str,
    publication_id: str,
    proof_hash: str | None,
    payload: dict[str, Any],
    source: str,
    sequence: int,
    profile_name: str | None = None,
    etherscan_stage: str = "READY_FOR_SUBMISSION",
) -> AnchorIndexEntry:
    contract_address = str(payload.get("contract_address") or os.getenv("AFRITECH_CHAIN_CONTRACT_ADDRESS") or "")
    explorer_url = str(payload.get("explorer_url") or "") or None
    chain_name = payload.get("chain_name")
    network = str(payload.get("network") or os.getenv("AFRITECH_CHAIN_MODE", "sepolia"))
    contract_explorer_url = _contract_explorer_url(profile_name or network, contract_address)
    if explorer_url is None and payload.get("transaction_hash"):
        try:
            profile = get_chain_profile(profile_name or network)
            explorer_url = f"{profile.explorer_base_url}{str(payload['transaction_hash']).removeprefix('0x')}"
        except Exception:
            explorer_url = None

    return AnchorIndexEntry(
        anchor_id=anchor_id,
        publication_id=publication_id,
        proof_hash=proof_hash,
        network=network,
        chain_id=int(payload["chain_id"]) if payload.get("chain_id") is not None else None,
        chain_name=str(chain_name) if chain_name is not None else None,
        contract_address=contract_address or None,
        transaction_hash=str(payload.get("transaction_hash") or payload.get("tx_hash") or ""),
        block_number=int(payload["block_number"]) if payload.get("block_number") is not None else None,
        explorer_url=explorer_url,
        anchor_mode=str(payload.get("anchor_mode") or payload.get("authority") or "unknown"),
        status=str(payload.get("status") or "unknown"),
        source=source,
        sequence=sequence,
        contract_explorer_url=contract_explorer_url,
        etherscan_verification_stage=etherscan_stage,
        meta=dict(payload.get("meta") or {}),
    )


def remember_publication(
    publication: BlockchainAnchorPublication | dict[str, Any],
    *,
    source: str = "api.publish_architecture_anchor",
) -> AnchorIndexEntry:
    payload = (
        dict(publication)
        if isinstance(publication, dict)
        else publication.canonical_dict()
    )
    anchor_id = str(payload.get("anchor_id") or "")
    publication_id = str(payload.get("publication_id") or "")
    proof_hash = payload.get("proof_hash")
    entry = _build_entry(
        anchor_id=anchor_id,
        publication_id=publication_id,
        proof_hash=str(proof_hash) if proof_hash is not None else None,
        payload=payload,
        source=source,
        sequence=len(ANCHOR_INDEX_STORE.list_entries()) + 1,
        profile_name=str(payload.get("network") or os.getenv("AFRITECH_CHAIN_MODE", "sepolia")),
    )
    return ANCHOR_INDEX_STORE.remember(entry)


def remember_chain_receipt(
    *,
    anchor_id: str,
    publication_id: str,
    proof_hash: str,
    chain_receipt: ChainReceipt | dict[str, Any],
    source: str = "proof.auto_anchor",
) -> AnchorIndexEntry:
    payload = _coerce_receipt(chain_receipt)
    payload.setdefault("anchor_mode", payload.get("authority", "runtime"))
    entry = _build_entry(
        anchor_id=anchor_id,
        publication_id=publication_id,
        proof_hash=proof_hash,
        payload=payload,
        source=source,
        sequence=len(ANCHOR_INDEX_STORE.list_entries()) + 1,
    )
    return ANCHOR_INDEX_STORE.remember(entry)


def build_anchor_index_snapshot() -> dict[str, Any]:
    entries = [entry.canonical_dict() for entry in ANCHOR_INDEX_STORE.list_entries()]
    latest = ANCHOR_INDEX_STORE.latest()
    return {
        "classification": "BLOCKCHAIN_ANCHOR_INDEX",
        "status": "READY",
        "count": len(entries),
        "latest": None if latest is None else latest.canonical_dict(),
        "entries": entries,
        "backend": ANCHOR_INDEX_STORE.describe(),
        "authority_boundary": "indexing_is_read_only_and_does_not_define_truth",
    }


def build_anchor_stream_snapshot() -> dict[str, Any]:
    stream = ANCHOR_EVENT_SUBSCRIBER.snapshot()
    stream["broadcast"] = ANCHOR_STREAM_HUB.snapshot()
    stream["streaming_policy"] = {
        "classification": "BLOCKCHAIN_ANCHOR_STREAMING_POLICY",
        "primary_transport": "websocket",
        "polling_role": "operator_backfill_only",
        "replay_required": True,
        "polling_is_primary": False,
        "authority_boundary": "streaming_policy_is_observational_only",
    }
    stream["authority_boundary"] = "event_subscription_is_read_only_and_indexing_only"
    return stream


def build_anchor_stream_replay(after_sequence: int = 0, limit: int = 50) -> dict[str, Any]:
    events = ANCHOR_STREAM_HUB.replay_after(after_sequence=after_sequence, limit=limit)
    return {
        "classification": "BLOCKCHAIN_ANCHOR_STREAM_REPLAY",
        "status": "READY",
        "after_sequence": after_sequence,
        "limit": limit,
        "count": len(events),
        "events": events,
        "stream": build_anchor_stream_snapshot(),
        "authority_boundary": "stream_replay_is_read_only_and_indexing_only",
    }


def build_anchor_detail(anchor_id: str) -> dict[str, Any]:
    try:
        entry = ANCHOR_INDEX_STORE.load(anchor_id)
    except KeyError:
        return {
            "classification": "BLOCKCHAIN_ANCHOR_DETAIL",
            "status": "NOT_FOUND",
            "anchor_id": anchor_id,
            "authority_boundary": "indexing_is_read_only_and_does_not_define_truth",
        }

    return {
        "classification": "BLOCKCHAIN_ANCHOR_DETAIL",
        "status": "READY",
        "entry": entry.canonical_dict(),
        "related_entries": [
            related.canonical_dict()
            for related in ANCHOR_INDEX_STORE.find_by_anchor_id(anchor_id)
        ],
        "authority_boundary": "indexing_is_read_only_and_does_not_define_truth",
    }


def build_evidence_consistency_policy() -> dict[str, Any]:
    return {
        "classification": "BLOCKCHAIN_EVIDENCE_CONSISTENCY_POLICY",
        "status": "READY",
        "invariants": list(EVIDENCE_CONSISTENCY_INVARIANTS),
        "resolution_strategies": CONFLICT_RESOLUTION_STRATEGIES,
        "streaming_policy": {
            "primary_transport": "websocket",
            "replay_endpoint": "/public/architecture/anchors/stream/replay",
            "poll_endpoint_role": "operator_backfill_only",
            "public_clients_should_use": [
                "/public/architecture/anchors/stream/ws",
                "/public/architecture/anchors/stream/replay",
            ],
        },
        "mainnet_gate": {
            "required_default_networks": ["sepolia", "base-sepolia"],
            "requires_no_divergence": True,
            "requires_required_network_coverage": True,
            "requires_websocket_streaming_policy": True,
        },
        "authority_boundary": "evidence_policy_constrains_observation_not_truth",
    }


def build_evidence_operational_semantics() -> dict[str, Any]:
    states = list(EVIDENCE_LIFECYCLE_STATES)
    transitions = list(EVIDENCE_OPERATIONAL_TRANSITIONS)
    terminal_states = {
        "DIVERGENT": {
            "state": "DIVERGENT_REVIEW",
            "mainnet_blocking": True,
            "resolution_strategy": CONFLICT_RESOLUTION_STRATEGIES["DIVERGENT"],
        },
        "PARTIAL": {
            "state": "PARTIAL_WAITING",
            "mainnet_blocking": True,
            "resolution_strategy": CONFLICT_RESOLUTION_STRATEGIES["PARTIAL"],
        },
        "SINGLE_NETWORK": {
            "state": "SINGLE_NETWORK_WAITING",
            "mainnet_blocking": True,
            "resolution_strategy": CONFLICT_RESOLUTION_STRATEGIES["SINGLE_NETWORK"],
        },
        "RECONCILED": {
            "state": "MAINNET_GATE_ELIGIBLE",
            "mainnet_blocking": False,
            "resolution_strategy": CONFLICT_RESOLUTION_STRATEGIES["RECONCILED"],
        },
    }
    semantics_payload = {
        "states": states,
        "transitions": transitions,
        "invariants": list(EVIDENCE_CONSISTENCY_INVARIANTS),
        "terminal_states": terminal_states,
    }
    return {
        "classification": "BLOCKCHAIN_EVIDENCE_OPERATIONAL_SEMANTICS",
        "status": "READY",
        "semantics_hash": _json_hash(semantics_payload),
        "lifecycle": {
            "canonical_flow": [state["id"] for state in states],
            "initial_state": "GOVERNED_DECISION",
            "verification_state": "PUBLICLY_VERIFIABLE",
        },
        "states": states,
        "transitions": transitions,
        "terminal_states": terminal_states,
        "truth_model": {
            "truth_authority": "Replay/Proof",
            "publication_evidence": "Blockchain",
            "visibility_surface": "Explorer/API",
            "control_surface": "Mainnet promotion gate",
            "forbidden_authorities": ["Blockchain", "Explorer", "Reconciliation", "Promotion gate"],
        },
        "public_surfaces": {
            "policy": "/public/architecture/evidence/policy",
            "reconciliation": "/public/architecture/anchors/reconciliation",
            "resolution": "/public/architecture/anchors/reconciliation/resolution",
            "stream": "/public/architecture/anchors/stream/ws",
            "replay": "/public/architecture/anchors/stream/replay",
            "mainnet_gate": "/public/architecture/anchors/mainnet-promotion-gate",
            "explorer": "/public/architecture/anchors/explorer",
        },
        "authority_boundary": "operational_semantics_define_evidence_behavior_not_truth",
    }


def build_governed_evidence_protocol() -> dict[str, Any]:
    policy = build_evidence_consistency_policy()
    semantics = build_evidence_operational_semantics()
    governance_artifacts = [
        {
            **artifact,
            "sha256": _file_sha256(artifact["path"]),
        }
        for artifact in GOVERNED_EVIDENCE_GOVERNANCE_ARTIFACTS
    ]
    protocol_contract = {
        "protocol_version": GOVERNED_EVIDENCE_PROTOCOL_VERSION,
        "classification": "GOVERNED_EVIDENCE_OPERATING_PROTOCOL",
        "semantics_hash": semantics["semantics_hash"],
        "policy_hash": _json_hash(
            {
                "invariants": policy["invariants"],
                "resolution_strategies": policy["resolution_strategies"],
                "streaming_policy": policy["streaming_policy"],
                "mainnet_gate": policy["mainnet_gate"],
            }
        ),
        "governance_artifacts": governance_artifacts,
        "public_surfaces": {
            "protocol": "/public/architecture/evidence/protocol",
            "semantics": "/public/architecture/evidence/semantics",
            "policy": "/public/architecture/evidence/policy",
            "reconciliation": "/public/architecture/anchors/reconciliation",
            "resolution": "/public/architecture/anchors/reconciliation/resolution",
            "stream": "/public/architecture/anchors/stream/ws",
            "replay": "/public/architecture/anchors/stream/replay",
            "mainnet_gate": "/public/architecture/anchors/mainnet-promotion-gate",
            "explorer": "/public/architecture/anchors/explorer",
            "adr_contract_link": "/public/architecture/adr/{adr_id}/contract-link",
        },
    }
    return {
        **protocol_contract,
        "status": (
            "READY"
            if all(item["sha256"] for item in governance_artifacts)
            else "GOVERNANCE_ARTIFACTS_INCOMPLETE"
        ),
        "protocol_hash": _json_hash(protocol_contract),
        "system_identity": {
            "name": "Governed Evidence Operating Platform",
            "category": "platform_protocol_governance_combined",
            "definition": (
                "deterministic_replayable_multi_network_evidence_system_with_governance_"
                "invariants_formal_semantics_conflict_resolution_and_promotion_control"
            ),
        },
        "authority_model": semantics["truth_model"],
        "lifecycle": semantics["lifecycle"],
        "governance_model": {
            "chain": ["ADR", "RULE", "BIND", "CI validator"],
            "validator": "afritech.ci.afritech_governed_evidence_protocol_validator",
            "required_validators": [
                "afritech.ci.afritech_blockchain_anchor_validator",
                "afritech.ci.afritech_blockchain_anchor_realtime_validator",
                "afritech.ci.afritech_governed_evidence_protocol_validator",
            ],
            "failure_rule": "missing_protocol_capability_or_governance_artifact_fails_ci",
        },
        "capabilities": [
            "deterministic_proof_hashing",
            "blockchain_publication_evidence",
            "websocket_first_observation",
            "stream_replay",
            "persistent_anchor_indexing",
            "cross_network_reconciliation",
            "conflict_resolution_semantics",
            "mainnet_promotion_gating",
            "adr_hash_contract_linking",
            "public_explorer_visibility",
        ],
        "authority_boundary": "protocol_combines_platform_and_governance_without_redefining_truth",
    }


def _resolution_strategy_for_status(status: str) -> dict[str, Any]:
    strategy = CONFLICT_RESOLUTION_STRATEGIES.get(
        status,
        CONFLICT_RESOLUTION_STRATEGIES["DIVERGENT"],
    )
    return dict(strategy)


def build_cross_network_anchor_reconciliation() -> dict[str, Any]:
    entries = list(ANCHOR_INDEX_STORE.list_entries())
    grouped: dict[str, list[AnchorIndexEntry]] = {}
    for entry in entries:
        key = entry.proof_hash or entry.anchor_id
        grouped.setdefault(key, []).append(entry)

    expected_networks = [profile.network for profile in list_chain_profiles()]
    reconciliations: list[dict[str, Any]] = []
    for proof_hash, grouped_entries in grouped.items():
        by_network = {entry.network: entry.canonical_dict() for entry in grouped_entries}
        network_count = len(by_network)
        first_entry = grouped_entries[0]
        live_networks = sorted({entry.network for entry in grouped_entries if entry.status in {"live", "CONFIRMED"}})
        missing_networks = [network for network in expected_networks if network not in by_network]
        anchor_ids = sorted({entry.anchor_id for entry in grouped_entries})
        publication_ids = sorted({entry.publication_id for entry in grouped_entries})
        contract_addresses = sorted(
            {
                entry.contract_address
                for entry in grouped_entries
                if entry.contract_address
            }
        )
        conflicts: list[dict[str, Any]] = []
        if len(anchor_ids) > 1:
            conflicts.append({"field": "anchor_id", "values": anchor_ids})
        if len(contract_addresses) > 1:
            conflicts.append({"field": "contract_address", "values": contract_addresses})
        reconciled = network_count > 1 and not conflicts and len(live_networks) == network_count
        if conflicts:
            reconciliation_status = "DIVERGENT"
        elif reconciled:
            reconciliation_status = "RECONCILED"
        elif network_count > 1:
            reconciliation_status = "PARTIAL"
        else:
            reconciliation_status = "SINGLE_NETWORK"
        resolution_strategy = _resolution_strategy_for_status(reconciliation_status)
        reconciliations.append(
            {
                "proof_hash": proof_hash,
                "anchor_id": first_entry.anchor_id,
                "publication_id": first_entry.publication_id,
                "publication_ids": publication_ids,
                "network_count": network_count,
                "expected_networks": expected_networks,
                "observed_networks": sorted(by_network),
                "missing_networks": missing_networks,
                "live_networks": live_networks,
                "reconciled": reconciled,
                "reconciliation_status": reconciliation_status,
                "invariants": list(EVIDENCE_CONSISTENCY_INVARIANTS),
                "conflicts": conflicts,
                "resolution_strategy": resolution_strategy,
                "mainnet_blocking": bool(resolution_strategy["mainnet_blocking"]),
                "networks": by_network,
                "authority_boundary": "cross_network_reconciliation_is_read_only_and_indexing_only",
            }
        )

    divergent = [item for item in reconciliations if item["reconciliation_status"] == "DIVERGENT"]
    partial = [item for item in reconciliations if item["reconciliation_status"] == "PARTIAL"]
    return {
        "classification": "BLOCKCHAIN_ANCHOR_CROSS_NETWORK_RECONCILIATION",
        "status": "READY",
        "expected_networks": expected_networks,
        "invariants": list(EVIDENCE_CONSISTENCY_INVARIANTS),
        "resolution_strategies": CONFLICT_RESOLUTION_STRATEGIES,
        "entries": reconciliations,
        "divergent_count": len(divergent),
        "partial_count": len(partial),
        "reconciled_count": sum(1 for item in reconciliations if item["reconciliation_status"] == "RECONCILED"),
        "authority_boundary": "cross_network_reconciliation_is_read_only_and_indexing_only",
    }


def _required_mainnet_gate_networks() -> list[str]:
    raw = os.getenv("AFRITECH_MAINNET_PROMOTION_REQUIRED_NETWORKS")
    if raw:
        networks = [item.strip() for item in raw.split(",") if item.strip()]
        if networks:
            return networks
    return ["sepolia", "base-sepolia"]


def build_mainnet_promotion_gate() -> dict[str, Any]:
    reconciliation = build_cross_network_anchor_reconciliation()
    stream = build_anchor_stream_snapshot()
    required_networks = _required_mainnet_gate_networks()
    entries = reconciliation["entries"]
    blocking_findings: list[dict[str, Any]] = []

    if not entries:
        blocking_findings.append(
            {
                "code": "NO_RECONCILIATION_EVIDENCE",
                "severity": "BLOCKING",
                "detail": "no anchor evidence has been observed for reconciliation",
            }
        )

    for entry in entries:
        missing_required = [
            network for network in required_networks if network not in entry["observed_networks"]
        ]
        if entry["reconciliation_status"] == "DIVERGENT":
            blocking_findings.append(
                {
                    "code": "DIVERGENT_EVIDENCE",
                    "severity": "BLOCKING",
                    "proof_hash": entry["proof_hash"],
                    "conflicts": entry["conflicts"],
                    "resolution_strategy": entry["resolution_strategy"],
                }
            )
        if missing_required:
            blocking_findings.append(
                {
                    "code": "MISSING_REQUIRED_NETWORK_OBSERVATION",
                    "severity": "BLOCKING",
                    "proof_hash": entry["proof_hash"],
                    "missing_networks": missing_required,
                    "required_networks": required_networks,
                }
            )

    streaming_policy = stream.get("streaming_policy", {})
    if streaming_policy.get("primary_transport") != "websocket":
        blocking_findings.append(
            {
                "code": "WEBSOCKET_STREAMING_NOT_PRIMARY",
                "severity": "BLOCKING",
                "detail": "mainnet promotion requires websocket-first observation",
            }
        )

    approved = not blocking_findings
    return {
        "classification": "BLOCKCHAIN_MAINNET_PROMOTION_GATE",
        "status": "APPROVED_FOR_MAINNET_PUBLICATION" if approved else "BLOCKED",
        "approved": approved,
        "required_networks": required_networks,
        "blocking_findings": blocking_findings,
        "reconciliation_summary": {
            "divergent_count": reconciliation["divergent_count"],
            "partial_count": reconciliation["partial_count"],
            "reconciled_count": reconciliation["reconciled_count"],
            "entry_count": len(entries),
        },
        "streaming_policy": streaming_policy,
        "promotion_rule": (
            "mainnet_promotion_requires_no_divergence_required_pre_mainnet_coverage_and_websocket_first_observation"
        ),
        "authority_boundary": "mainnet_gate_blocks_promotion_but_does_not_define_truth",
    }


def build_etherscan_contract_verification_report(
    *,
    profile_name: str | None = None,
) -> dict[str, Any]:
    profile_name = profile_name or os.getenv("AFRITECH_CHAIN_MODE", "sepolia")
    health = chain_health(profile_name=profile_name)
    contract_address = os.getenv("AFRITECH_CHAIN_CONTRACT_ADDRESS", "")
    contract_explorer_url = _contract_explorer_url(profile_name, contract_address or None)
    contract_configured = bool(contract_address) and contract_address.lower() not in PLACEHOLDER_CONTRACT_ADDRESSES
    latest = ANCHOR_INDEX_STORE.latest()
    verification_ready = contract_configured and bool(contract_explorer_url)
    stage = "READY_FOR_SUBMISSION"
    if contract_configured and health.get("status") == "ok" and latest is not None and latest.status == "live":
        stage = "CHAIN_READY"
    if contract_configured and os.getenv("AFRITECH_CHAIN_ETHERSCAN_VERIFIED", "false").lower() == "true":
        stage = "VERIFIED_ON_ETHERSCAN"

    return {
        "classification": "ETHERSCAN_CONTRACT_VERIFICATION_REPORT",
        "status": "READY",
        "network": profile_name,
        "chain_health": health,
        "contract_address": contract_address or None,
        "contract_explorer_url": contract_explorer_url,
        "contract_name": "ArchitectureAnchor",
        "contract_source_path": "afritech/contracts/ArchitectureAnchor.sol",
        "abi_fingerprint": _abi_fingerprint(),
        "verification_stage": stage,
        "verification_ready": verification_ready,
        "latest_anchor": None if latest is None else latest.canonical_dict(),
        "authority_boundary": "contract_verification_packaging_is_read_only",
    }


def build_blockchain_architecture_map() -> dict[str, Any]:
    return {
        "classification": "AFRITECH_BLOCKCHAIN_ARCHITECTURE_MAP",
        "status": "READY",
        "authority_boundary": "map_is_documentation_and_observation_only",
        "stack": [
            "AfriTech API auto-anchor system",
            "Anchor indexer",
            "WebSocket stream hub",
            "ArchitectureAnchor smart contract",
            "Ethereum Sepolia / Mainnet",
            "Etherscan contract and transaction surfaces",
            "External anchor explorer app",
            "Public anchor dashboard",
        ],
        "supported_networks": ["sepolia", "base-sepolia", "mainnet"],
        "persistence_modes": ["memory", "file", "redis", "postgres"],
        "components": [
            {
                "name": "API integration",
                "route": "/v1/architecture/anchor/blockchain",
                "purpose": "Publish architecture proofs and record anchor publications.",
            },
            {
                "name": "Auto-anchor",
                "route": "/public/architecture/proof",
                "purpose": "Attach live receipts to proof generation when enabled.",
            },
            {
                "name": "Event indexing",
                "route": "/public/architecture/anchors",
                "purpose": "Expose deterministic in-process anchor event index.",
            },
            {
                "name": "Event subscription",
                "route": "/public/architecture/anchors/stream/ws",
                "purpose": "Stream contract events over WebSocket and hydrate the read-only index.",
            },
            {
                "name": "Anchor status",
                "route": "/public/architecture/anchors/status",
                "purpose": "Expose auto-anchor state and verification readiness.",
            },
            {
                "name": "Cross-network reconciliation",
                "route": "/public/architecture/anchors/reconciliation",
                "purpose": "Compare anchor evidence across networks and enforce reconciliation invariants.",
            },
            {
                "name": "Evidence consistency policy",
                "route": "/public/architecture/evidence/policy",
                "purpose": "Expose formal reconciliation invariants and conflict resolution semantics.",
            },
            {
                "name": "Evidence operational semantics",
                "route": "/public/architecture/evidence/semantics",
                "purpose": "Expose the governed evidence lifecycle, transition guards, and authority model.",
            },
            {
                "name": "Governed evidence protocol",
                "route": "/public/architecture/evidence/protocol",
                "purpose": "Expose the combined platform, protocol, governance, and CI contract.",
            },
            {
                "name": "Mainnet promotion gate",
                "route": "/public/architecture/anchors/mainnet-promotion-gate",
                "purpose": "Block mainnet promotion until reconciliation and WebSocket observation gates pass.",
            },
            {
                "name": "Etherscan verification",
                "route": "/public/architecture/anchors/verification",
                "purpose": "Package the contract verification handoff and explorer links.",
            },
            {
                "name": "Anchor dashboard",
                "route": "/public/architecture/anchors/dashboard",
                "purpose": "Show latest publication, contract verification status, and index entries.",
            },
            {
                "name": "Anchor explorer",
                "route": "/public/architecture/anchors/explorer",
                "purpose": "External app for public anchor inspection and live event streaming.",
            },
        ],
        "promotion_plan": build_chain_promotion_plan(),
    }


def render_anchor_dashboard_html() -> str:
    snapshot = build_anchor_index_snapshot()
    verification = build_etherscan_contract_verification_report()
    stream = build_anchor_stream_snapshot()
    latest = snapshot["latest"] or {}
    rows = []
    for entry in snapshot["entries"]:
        rows.append(
            "<tr>"
            f"<td>{escape(str(entry['sequence']))}</td>"
            f"<td><code>{escape(str(entry['anchor_id']))}</code></td>"
            f"<td><code>{escape(str(entry['transaction_hash']))}</code></td>"
            f"<td>{escape(str(entry['network']))}</td>"
            f"<td>{escape(str(entry['status']))}</td>"
            f"<td>{escape(str(entry['source']))}</td>"
            "</tr>"
        )
    rows_html = "".join(rows) or (
        "<tr><td colspan='6'>No anchors indexed yet.</td></tr>"
    )
    latest_hash = latest.get("transaction_hash", "n/a")
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>AfriTech Architecture Anchor Dashboard</title>
    <style>
      :root {{ color-scheme: light; }}
      body {{ margin: 0; font-family: Inter, Arial, sans-serif; background: #f4f7fb; color: #102033; }}
      main {{ max-width: 1200px; margin: 0 auto; padding: 32px 20px 56px; }}
      h1 {{ margin: 0 0 8px; font-size: 30px; }}
      p {{ line-height: 1.5; }}
      .band {{ display: flex; flex-wrap: wrap; gap: 12px; margin: 16px 0 24px; }}
      .pill {{ background: #e8f1ff; color: #0c4a7f; padding: 8px 12px; border-radius: 999px; font-size: 13px; font-weight: 600; }}
      .grid {{ display: grid; gap: 16px; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); margin-bottom: 20px; }}
      .card {{ background: #fff; border: 1px solid #d8e0ea; border-radius: 8px; padding: 16px; box-shadow: 0 1px 2px rgba(16,24,40,.04); }}
      table {{ width: 100%; border-collapse: collapse; background: #fff; border: 1px solid #d8e0ea; border-radius: 8px; overflow: hidden; }}
      th, td {{ text-align: left; padding: 12px 10px; border-bottom: 1px solid #edf1f5; font-size: 14px; vertical-align: top; }}
      th {{ background: #f8fafc; font-size: 12px; text-transform: uppercase; letter-spacing: .03em; color: #5d7187; }}
      code {{ background: #eef3f7; padding: 2px 6px; border-radius: 4px; }}
      a {{ color: #185aa8; text-decoration: none; }}
      .small {{ color: #5d7187; font-size: 13px; }}
    </style>
  </head>
  <body>
    <main>
      <h1>Architecture Anchor Dashboard</h1>
      <p>Read-only view of anchor publications, contract verification readiness, and the blockchain publication surface.</p>
      <div class="band">
        <div class="pill">Indexed anchors: {snapshot['count']}</div>
        <div class="pill">Latest tx: <code>{escape(str(latest_hash))}</code></div>
        <div class="pill">Etherscan stage: {escape(str(verification['verification_stage']))}</div>
        <div class="pill">Backend: {escape(str(snapshot.get('backend', {}).get('backend', 'unknown')))}</div>
        <div class="pill">Stream: {escape(str(stream.get('status', 'unknown')))} / {escape(str(stream.get('transport', 'unknown')))}</div>
        <div class="pill">Clients: {escape(str(stream.get('broadcast', {}).get('connected_clients', 0)))}</div>
        <div class="pill"><a href="/public/architecture/anchors/verification">Verification packet</a></div>
        <div class="pill"><a href="/public/architecture/anchors/reconciliation">Cross-network reconciliation</a></div>
      </div>
      <div class="grid">
        <div class="card">
          <strong>Latest publication</strong>
          <p class="small">Anchor <code>{escape(str(latest.get('anchor_id', 'n/a')))}</code></p>
          <p class="small">Network: {escape(str(latest.get('network', 'n/a')))}</p>
          <p class="small">Contract: {escape(str(latest.get('contract_address', 'n/a')))}</p>
          <p class="small">Explorer: {escape(str(latest.get('explorer_url', 'n/a')))}</p>
        </div>
        <div class="card">
          <strong>Contract verification</strong>
          <p class="small">Status: {escape(str(verification['verification_stage']))}</p>
          <p class="small">Contract explorer: {escape(str(verification['contract_explorer_url'] or 'n/a'))}</p>
          <p class="small">ABI fingerprint: <code>{escape(str(verification['abi_fingerprint']))}</code></p>
        </div>
      </div>
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Anchor</th>
            <th>Transaction</th>
            <th>Network</th>
            <th>Status</th>
            <th>Source</th>
          </tr>
        </thead>
        <tbody>
          {rows_html}
        </tbody>
      </table>
    </main>
  </body>
</html>"""


def _latest_index_block_for_network(network: str) -> int | None:
    blocks = [
        entry.block_number
        for entry in ANCHOR_INDEX_STORE.list_entries()
        if entry.network == network and entry.block_number is not None
    ]
    return max(blocks) if blocks else None


def _deployment_start_block(profile_name: str) -> int:
    raw = os.getenv(f"AFRITECH_CHAIN_CONTRACT_DEPLOYMENT_BLOCK_{profile_name.upper().replace('-', '_')}")
    if not raw:
        raw = os.getenv("AFRITECH_CHAIN_CONTRACT_DEPLOYMENT_BLOCK")
    if not raw:
        return 0
    try:
        return max(0, int(raw))
    except ValueError:
        return 0


@dataclass(frozen=True)
class AnchorEventSubscriptionStatus:
    classification: str
    status: str
    enabled: bool
    transport: str
    active_profiles: tuple[str, ...]
    streaming_profiles: tuple[str, ...]
    events_indexed: int
    last_blocks: dict[str, int | None]
    last_error: str | None = None

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "classification": self.classification,
            "status": self.status,
            "enabled": self.enabled,
            "transport": self.transport,
            "active_profiles": self.active_profiles,
            "streaming_profiles": self.streaming_profiles,
            "events_indexed": self.events_indexed,
            "last_blocks": self.last_blocks,
            "last_error": self.last_error,
            "authority_boundary": "event_subscription_is_read_only_and_indexing_only",
        }


class AnchorEventSubscriber:
    """Streams chain events and indexes them into the anchor read model."""

    def __init__(self, index_store: AnchorIndexStore) -> None:
        self.index_store = index_store
        self.enabled = os.getenv("AFRITECH_CHAIN_EVENT_SUBSCRIBER_ENABLED", "false").lower() == "true"
        self.transport = os.getenv("AFRITECH_CHAIN_EVENT_SUBSCRIBER_TRANSPORT", "websocket").lower()
        self.backfill_enabled = os.getenv("AFRITECH_CHAIN_EVENT_BACKFILL_ENABLED", "true").lower() == "true"
        self.reconnect_delay_seconds = float(os.getenv("AFRITECH_CHAIN_EVENT_RECONNECT_DELAY_SECONDS", "5"))
        self._stop_requested = False
        self._last_error: str | None = None
        self._tasks: list[asyncio.Task[None]] = []
        self._started_profiles: set[str] = set()

    def active_profiles(self) -> tuple[str, ...]:
        return tuple(profile.key for profile in list_chain_profiles())

    def _web3(self, rpc_url: str):
        try:
            from web3 import Web3
        except ModuleNotFoundError as exc:
            raise AnchorIndexBackendError("web3 is required for anchor event subscription") from exc
        return Web3(Web3.HTTPProvider(rpc_url))

    def _web3_ws(self, ws_url: str):
        try:
            from web3 import Web3
        except ModuleNotFoundError as exc:
            raise AnchorIndexBackendError("web3 is required for anchor event subscription") from exc
        provider = getattr(Web3, "LegacyWebSocketProvider", None)
        if provider is None:
            return Web3(Web3.HTTPProvider(ws_url))
        return Web3(provider(ws_url))

    def _subscription_topic(self) -> str:
        return self._subscription_topic_v1()

    def _subscription_topic_v1(self) -> str:
        try:
            from web3 import Web3
        except ModuleNotFoundError as exc:
            raise AnchorIndexBackendError("web3 is required for anchor event subscription") from exc
        return Web3.keccak(text="ProofAnchored(string,bytes32,address,uint256)").hex()

    def _subscription_topic_v2(self) -> str:
        try:
            from web3 import Web3
        except ModuleNotFoundError as exc:
            raise AnchorIndexBackendError("web3 is required for anchor event subscription") from exc
        return Web3.keccak(text="ProofAnchored(bytes32,bytes32,address,uint256,bytes32)").hex()

    def _build_entry_from_event(
        self,
        profile,
        event: Any,
        *,
        version: str = "v1",
        contract_address: str | None = None,
    ) -> AnchorIndexEntry:
        args = _event_args(event)
        anchor_id_value = _event_arg(args, "anchorId", "")
        anchor_id = _hex_value(anchor_id_value) if version == "v2" else str(anchor_id_value)
        proof_hash_value = _hex_value(_event_arg(args, "proofHash"))
        context_value = _event_arg(args, "context", b"")

        transaction_hash = _hex_value(_event_value(event, "transactionHash"))
        if transaction_hash and not transaction_hash.startswith("0x"):
            transaction_hash = f"0x{transaction_hash}"
        resolved_contract_address = contract_address or os.getenv(
            "AFRITECH_CHAIN_CONTRACT_ADDRESS_V2" if version == "v2" else "AFRITECH_CHAIN_CONTRACT_ADDRESS"
        )

        payload = {
            "anchor_id": anchor_id,
            "publication_id": f"{anchor_id}:{transaction_hash}",
            "proof_hash": proof_hash_value,
            "network": profile.network,
            "chain_id": profile.chain_id,
            "chain_name": profile.chain_name,
            "contract_address": resolved_contract_address,
            "transaction_hash": transaction_hash,
            "block_number": _int_or_default(_event_value(event, "blockNumber")),
            "explorer_url": f"{profile.explorer_base_url}{transaction_hash.removeprefix('0x')}",
            "anchor_mode": "smart_contract",
            "status": "live",
            "source": "event_subscriber.websocket",
            "sequence": len(self.index_store.list_entries()) + 1,
            "contract_explorer_url": _contract_explorer_url(profile.key, resolved_contract_address),
            "etherscan_verification_stage": "EVENT_STREAMED",
            "meta": {
                "contract_version": version,
                "context": _bytes32_context(context_value) if version == "v2" else None,
                "context_bytes32": _hex_value(context_value) if version == "v2" else None,
            },
        }
        return _entry_from_row(payload)

    def _configured_contracts(self) -> tuple[tuple[str, str, list[dict[str, Any]]], ...]:
        contracts: list[tuple[str, str, list[dict[str, Any]]]] = []
        v1_address = os.getenv("AFRITECH_CHAIN_CONTRACT_ADDRESS")
        if v1_address:
            contracts.append(("v1", v1_address, ARCHITECTURE_ANCHOR_ABI))
        v2_address = os.getenv("AFRITECH_CHAIN_CONTRACT_ADDRESS_V2")
        if v2_address:
            contracts.append(("v2", v2_address, ARCHITECTURE_ANCHOR_V2_ABI))
        return tuple(contracts)

    def _backfill_once(self, profile_name: str) -> int:
        profile = get_chain_profile(profile_name)
        rpc_url = os.getenv(profile.rpc_env_var)
        if not rpc_url:
            return 0

        configured_contracts = self._configured_contracts()
        if not configured_contracts:
            return 0

        web3 = self._web3(rpc_url)
        if not web3.is_connected():
            raise AnchorIndexBackendError(f"anchor event subscriber cannot connect to {profile_name}")
        from_block = _latest_index_block_for_network(profile.network)
        if from_block is None:
            from_block = _deployment_start_block(profile_name)
        else:
            from_block += 1

        indexed = 0
        for version, contract_address, abi in configured_contracts:
            contract = web3.eth.contract(
                address=web3.to_checksum_address(contract_address),
                abi=abi,
            )
            try:
                events = contract.events.ProofAnchored().get_logs(from_block=from_block, to_block="latest")
            except TypeError:
                events = contract.events.ProofAnchored().get_logs(fromBlock=from_block, toBlock="latest")

            for event in events:
                entry = self._build_entry_from_event(
                    profile,
                    event,
                    version=version,
                    contract_address=contract_address,
                )
                if not entry.anchor_id:
                    continue
                if any(
                    existing.anchor_id == entry.anchor_id
                    and existing.network == entry.network
                    and existing.transaction_hash == entry.transaction_hash
                    for existing in self.index_store.list_entries()
                ):
                    continue
                self.index_store.remember(entry)
                indexed += 1

        self._last_error = None
        return indexed

    def poll_once(self, profile_name: str) -> int:
        return self.sync_once(profile_name)

    def sync_once(self, profile_name: str) -> int:
        return self._backfill_once(profile_name)

    def poll_all(self) -> dict[str, int]:
        return self.sync_all()

    def sync_all(self) -> dict[str, int]:
        results: dict[str, int] = {}
        for profile_name in self.active_profiles():
            try:
                results[profile_name] = self.sync_once(profile_name)
            except Exception as exc:
                self._last_error = str(exc)
                results[profile_name] = 0
        return results

    async def _stream_profile(self, profile_name: str) -> None:
        if not self.enabled or self.transport != "websocket":
            return

        profile = get_chain_profile(profile_name)
        ws_url = resolve_chain_ws_url(profile)
        web3 = self._web3_ws(ws_url)
        configured_contracts = self._configured_contracts()
        if not configured_contracts:
            return

        if self.backfill_enabled:
            try:
                self.sync_once(profile_name)
            except Exception as exc:
                self._last_error = str(exc)

        try:
            import websockets
        except ModuleNotFoundError as exc:
            raise AnchorIndexBackendError("websockets is required for anchor event subscription") from exc

        while not self._stop_requested:
            try:
                if not web3.is_connected():
                    raise AnchorIndexBackendError(f"anchor websocket subscriber cannot connect to {profile_name}")
                async with websockets.connect(ws_url, ping_interval=20, ping_timeout=20) as websocket:
                    await websocket.send(
                        json.dumps(
                            {
                                "jsonrpc": "2.0",
                                "id": 1,
                                "method": "eth_subscribe",
                                "params": [
                                    "logs",
                                    {
                                        "address": [contract[1] for contract in configured_contracts],
                                        "topics": [[self._subscription_topic_v1(), self._subscription_topic_v2()]],
                                    },
                                ],
                            }
                        )
                    )
                    response = json.loads(await websocket.recv())
                    if response.get("error"):
                        raise AnchorIndexBackendError(str(response["error"]))

                    self._started_profiles.add(profile_name)
                    self._last_error = None
                    contracts = {
                        address.lower(): (
                            version,
                            web3.eth.contract(
                                address=web3.to_checksum_address(address),
                                abi=abi,
                            ),
                        )
                        for version, address, abi in configured_contracts
                    }
                    while not self._stop_requested:
                        message = json.loads(await websocket.recv())
                        if message.get("method") != "eth_subscription":
                            continue
                        params = message.get("params") or {}
                        if params.get("subscription") is None:
                            continue
                        log = params.get("result") or {}
                        log_address = str(log.get("address") or "").lower()
                        contract_pair = contracts.get(log_address)
                        if not contract_pair:
                            continue
                        version, contract = contract_pair
                        try:
                            event = contract.events.ProofAnchored().process_log(log)
                        except Exception:
                            continue
                        entry = self._build_entry_from_event(
                            profile,
                            event,
                            version=version,
                            contract_address=log.get("address"),
                        )
                        if any(
                            existing.anchor_id == entry.anchor_id
                            and existing.network == entry.network
                            and existing.transaction_hash == entry.transaction_hash
                            for existing in self.index_store.list_entries()
                        ):
                            continue
                        self.index_store.remember(entry)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                self._last_error = str(exc)
                await asyncio.sleep(self.reconnect_delay_seconds)

    async def start(self) -> None:
        if not self.enabled or self.transport != "websocket":
            return
        if self._tasks:
            return
        self._stop_requested = False
        self._tasks = [
            asyncio.create_task(self._stream_profile(profile_name))
            for profile_name in self.active_profiles()
        ]

    async def stop(self) -> None:
        self._stop_requested = True
        while self._tasks:
            task = self._tasks.pop()
            task.cancel()
            with contextlib.suppress(Exception):
                await task
        self._started_profiles.clear()

    def status(self) -> AnchorEventSubscriptionStatus:
        return AnchorEventSubscriptionStatus(
            classification="BLOCKCHAIN_ANCHOR_EVENT_SUBSCRIPTION_STATUS",
            status="READY" if self.enabled else "DISABLED",
            enabled=self.enabled,
            transport=self.transport,
            active_profiles=self.active_profiles(),
            streaming_profiles=tuple(sorted(self._started_profiles)),
            events_indexed=len(self.index_store.list_entries()),
            last_blocks={profile: _latest_index_block_for_network(get_chain_profile(profile).network) for profile in self.active_profiles()},
            last_error=self._last_error,
        )

    def snapshot(self) -> dict[str, Any]:
        return self.status().canonical_dict()


ANCHOR_EVENT_SUBSCRIBER = AnchorEventSubscriber(ANCHOR_INDEX_STORE)
AnchorChainEventSubscriber = AnchorEventSubscriber


__all__ = [
    "ANCHOR_EVENT_SUBSCRIBER",
    "ANCHOR_STREAM_HUB",
    "ANCHOR_INDEX_STORE",
    "AnchorChainEventSubscriber",
    "AnchorEventSubscriptionStatus",
    "AnchorIndexEntry",
    "AnchorIndexBackend",
    "AnchorIndexBackendError",
    "AnchorIndexStore",
    "InMemoryAnchorIndexBackend",
    "JsonFileAnchorIndexBackend",
    "PostgresAnchorIndexBackend",
    "RedisAnchorIndexBackend",
    "build_anchor_detail",
    "build_anchor_index_snapshot",
    "build_anchor_stream_replay",
    "build_anchor_stream_snapshot",
    "build_blockchain_architecture_map",
    "build_cross_network_anchor_reconciliation",
    "build_evidence_consistency_policy",
    "build_evidence_operational_semantics",
    "build_governed_evidence_protocol",
    "build_etherscan_contract_verification_report",
    "build_mainnet_promotion_gate",
    "remember_chain_receipt",
    "remember_publication",
    "render_anchor_dashboard_html",
]
