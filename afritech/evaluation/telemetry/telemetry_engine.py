"""
afritech/evaluation/telemetry/telemetry_engine.py

Telemetry Engine
================

Provides execution observability for the constitutional runtime.

Responsibilities:
- Capture execution lifecycle events
- Record structured telemetry data
- Provide lightweight metrics tracking
- Support audit and replay inspection
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib
import json


# -----------------------------------------------------------------
# TELEMETRY ERROR
# -----------------------------------------------------------------

class TelemetryError(Exception):
    pass


# -----------------------------------------------------------------
# TELEMETRY RECORD
# -----------------------------------------------------------------

class TelemetryRecord:

    def __init__(
        self,
        event_type: str,
        data: Dict[str, Any],
    ):
        self.event_type = event_type
        self.data = data

        self.timestamp = datetime.utcnow().isoformat() + "Z"
        self.record_hash = self._compute_hash()

    # -------------------------------------------------------------
    # HASH
    # -------------------------------------------------------------

    def _canonical_json(self, data: Dict[str, Any]) -> str:
        return json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":")
        )

    def _compute_hash(self) -> str:
        payload = {
            "event_type": self.event_type,
            "data": self.data,
            "timestamp": self.timestamp
        }

        return hashlib.sha256(
            self._canonical_json(payload).encode()
        ).hexdigest()

    # -------------------------------------------------------------
    # EXPORT
    # -------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "data": self.data,
            "timestamp": self.timestamp,
            "record_hash": self.record_hash
        }

    def __repr__(self):
        return f"<TelemetryRecord {self.event_type} {self.record_hash[:10]}...>"


# -----------------------------------------------------------------
# TELEMETRY ENGINE
# -----------------------------------------------------------------

class TelemetryEngine:

    def __init__(
        self,
        max_buffer_size: int = 1000,
        event_bus: Optional[Any] = None
    ):
        """
        :param max_buffer_size: max in-memory records
        :param event_bus: optional real-time event bus
        """
        self.buffer: List[TelemetryRecord] = []
        self.max_buffer_size = max_buffer_size
        self.event_bus = event_bus

    # -----------------------------------------------------------------
    # RECORD EVENT
    # -----------------------------------------------------------------

    def record(
        self,
        event_type: str,
        data: Dict[str, Any]
    ) -> TelemetryRecord:

        if not isinstance(data, dict):
            raise TelemetryError("Telemetry data must be dict")

        record = TelemetryRecord(event_type, data)

        self._store(record)
        self._emit(record)

        return record

    # -----------------------------------------------------------------
    # STORE TELEMETRY
    # -----------------------------------------------------------------

    def _store(self, record: TelemetryRecord):
        self.buffer.append(record)

        # Prevent memory overflow
        if len(self.buffer) > self.max_buffer_size:
            self.buffer.pop(0)

    # -----------------------------------------------------------------
    # EXPORT BUFFER
    # -----------------------------------------------------------------

    def export(self) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self.buffer]

    # -----------------------------------------------------------------
    # CLEAR BUFFER
    # -----------------------------------------------------------------

    def clear(self):
        self.buffer.clear()

    # -----------------------------------------------------------------
    # EVENT EMISSION
    # -----------------------------------------------------------------

    def _emit(self, record: TelemetryRecord):
        if not self.event_bus:
            return

        try:
            import asyncio
            asyncio.create_task(
                self.event_bus.publish({
                    "type": "TELEMETRY_EVENT",
                    "event": record.to_dict()
                })
            )
        except Exception:
            pass  # never break runtime

    # -----------------------------------------------------------------
    # METRICS (BASIC)
    # -----------------------------------------------------------------

    def metrics(self) -> Dict[str, Any]:
        """
        Basic telemetry metrics
        """

        total_events = len(self.buffer)

        event_types = {}
        for r in self.buffer:
            event_types[r.event_type] = event_types.get(r.event_type, 0) + 1

        return {
            "total_events": total_events,
            "event_distribution": event_types
        }


# -----------------------------------------------------------------
# FACTORY
# -----------------------------------------------------------------

def create_telemetry_engine(
    event_bus: Optional[Any] = None
) -> TelemetryEngine:
    return TelemetryEngine(event_bus=event_bus)