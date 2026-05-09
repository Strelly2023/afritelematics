"""
afritech/network/rpc_client.py

RPC Client
==========

Transport-independent RPC execution layer for distributed nodes.

Responsibilities:
- Execute remote calls via pluggable transport
- Ensure deterministic request/response handling
- Provide retry + timeout resilience
- Normalize responses for consensus compatibility
"""

from __future__ import annotations

from typing import Dict, Any, Callable, Optional
import hashlib
import json
import time


# -----------------------------------------------------------------
# RPC ERROR
# -----------------------------------------------------------------

class RPCClientError(Exception):
    pass


# -----------------------------------------------------------------
# TRANSPORT TYPES
# -----------------------------------------------------------------

class TransportType:
    HTTP = "HTTP"
    LOCAL = "LOCAL"
    CUSTOM = "CUSTOM"


# -----------------------------------------------------------------
# RPC CLIENT
# -----------------------------------------------------------------

class RPCClient:

    def __init__(
        self,
        node_id: str,
        transport_fn: Callable[[Dict[str, Any]], Dict[str, Any]],
        transport_type: str = TransportType.CUSTOM,
        timeout: float = 5.0,
        retries: int = 2,
        retry_delay: float = 0.5,
    ):
        """
        :param node_id: identity of the remote node
        :param transport_fn: function executing the RPC call
        :param transport_type: type of transport (HTTP, LOCAL, CUSTOM)
        :param timeout: execution timeout (handled externally if needed)
        :param retries: retry attempts
        :param retry_delay: delay between retries
        """

        if not callable(transport_fn):
            raise RPCClientError("transport_fn must be callable")

        self.node_id = node_id
        self.transport_fn = transport_fn
        self.transport_type = transport_type
        self.timeout = timeout
        self.retries = retries
        self.retry_delay = retry_delay

    # -----------------------------------------------------------------
    # CANONICAL JSON (DETERMINISM)
    # -----------------------------------------------------------------

    def _canonical_json(self, data: Dict[str, Any]) -> str:
        return json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":"),
        )

    # -----------------------------------------------------------------
    # REQUEST HASH (TRACEABILITY)
    # -----------------------------------------------------------------

    def _hash_request(self, request: Dict[str, Any]) -> str:
        return hashlib.sha256(
            self._canonical_json(request).encode()
        ).hexdigest()

    # -----------------------------------------------------------------
    # EXECUTE
    # -----------------------------------------------------------------

    def execute(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform RPC execution with retry + normalization
        """

        request_hash = self._hash_request(request)
        last_error: Optional[str] = None

        for attempt in range(self.retries + 1):

            try:
                response = self.transport_fn(self._decorate_request(request, request_hash))

                if not isinstance(response, dict):
                    raise RPCClientError("Invalid response format (must be dict)")

                return self._normalize_response(response)

            except Exception as e:
                last_error = str(e)

                if attempt < self.retries:
                    time.sleep(self.retry_delay)
                else:
                    raise RPCClientError(
                        f"RPC execution failed on node {self.node_id}: {last_error}"
                    )

        raise RPCClientError("Unexpected RPC execution failure")

    # -----------------------------------------------------------------
    # REQUEST DECORATION
    # -----------------------------------------------------------------

    def _decorate_request(self, request: Dict[str, Any], request_hash: str) -> Dict[str, Any]:
        """
        Enrich request with metadata for traceability
        """
        return {
            **request,
            "_meta": {
                "node_id": self.node_id,
                "request_hash": request_hash,
                "transport": self.transport_type,
            }
        }

    # -----------------------------------------------------------------
    # NORMALIZATION
    # -----------------------------------------------------------------

    def _normalize_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure response fits consensus requirements
        """

        # Already aligned with ExecutionResult
        if "result_hash" in data:
            return data

        # Wrapped response
        if "result" in data and isinstance(data["result"], dict):
            result = data["result"]

            if "result_hash" in result:
                return result

            return {
                **result,
                "result_hash": self._fallback_hash(result)
            }

        # Entire payload fallback
        return {
            **data,
            "result_hash": self._fallback_hash(data)
        }

    # -----------------------------------------------------------------
    # FALLBACK HASH
    # -----------------------------------------------------------------

    def _fallback_hash(self, data: Dict[str, Any]) -> str:
        return hashlib.sha256(
            self._canonical_json(data).encode()
        ).hexdigest()

    # -----------------------------------------------------------------
    # INFO
    # -----------------------------------------------------------------

    def info(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "transport": self.transport_type,
            "timeout": self.timeout,
            "retries": self.retries,
        }

    # -----------------------------------------------------------------
    # STRING
    # -----------------------------------------------------------------

    def __repr__(self):
        return f"<RPCClient node={self.node_id} transport={self.transport_type}>"