"""
afritech/network/node/http_node_client.py

HTTP Node Client
================

Executes requests against remote AfriTech nodes over HTTP.

Responsibilities:
- Send execution requests to remote nodes
- Normalize responses into consensus-compatible format
- Handle timeouts, retries, and failures
"""

from __future__ import annotations

from typing import Dict, Any, Optional
import requests
import hashlib
import json
import time


# -----------------------------------------------------------------
# CLIENT ERROR
# -----------------------------------------------------------------

class HttpNodeClientError(Exception):
    pass


# -----------------------------------------------------------------
# HTTP NODE CLIENT
# -----------------------------------------------------------------

class HttpNodeClient:
    """
    HTTP-based node client for distributed execution
    """

    def __init__(
        self,
        node_id: str,
        base_url: str,
        timeout: float = 5.0,
        retries: int = 2,
        retry_delay: float = 0.5,
    ):
        """
        :param node_id: logical node identifier
        :param base_url: node endpoint (e.g., http://localhost:8001)
        :param timeout: request timeout in seconds
        :param retries: retry attempts on failure
        :param retry_delay: delay between retries
        """
        self.node_id = node_id
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.retries = retries
        self.retry_delay = retry_delay

    # -----------------------------------------------------------------
    # CANONICAL JSON (DETERMINISTIC TRANSMISSION)
    # -----------------------------------------------------------------

    def _canonical_json(self, data: Dict[str, Any]) -> str:
        return json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":"),
        )

    # -----------------------------------------------------------------
    # PAYLOAD HASH (OPTIONAL TRACEABILITY)
    # -----------------------------------------------------------------

    def _hash_payload(self, payload: Dict[str, Any]) -> str:
        return hashlib.sha256(
            self._canonical_json(payload).encode()
        ).hexdigest()

    # -----------------------------------------------------------------
    # EXECUTION (REMOTE CALL)
    # -----------------------------------------------------------------

    def execute(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sends execution request to remote node
        """

        url = f"{self.base_url}/execute"

        payload_hash = self._hash_payload(request)

        last_error: Optional[str] = None

        for attempt in range(self.retries + 1):
            try:
                response = requests.post(
                    url,
                    json=request,
                    timeout=self.timeout,
                    headers={
                        "Content-Type": "application/json",
                        "X-Node-ID": self.node_id,
                        "X-Payload-Hash": payload_hash,
                    },
                )

                # -----------------------------------------------------
                # HTTP STATUS CHECK
                # -----------------------------------------------------
                if response.status_code != 200:
                    raise HttpNodeClientError(
                        f"Invalid HTTP status: {response.status_code}"
                    )

                data = response.json()

                if not isinstance(data, dict):
                    raise HttpNodeClientError(
                        "Invalid response format (not dict)"
                    )

                return self._normalize_response(data)

            except Exception as e:
                last_error = str(e)

                if attempt < self.retries:
                    time.sleep(self.retry_delay)
                else:
                    raise HttpNodeClientError(
                        f"Node {self.node_id} failed after retries: {last_error}"
                    )

        # Should never reach here
        raise HttpNodeClientError("Unexpected execution failure")

    # -----------------------------------------------------------------
    # RESPONSE NORMALIZATION
    # -----------------------------------------------------------------

    def _normalize_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure response matches consensus expectations
        """

        # If remote already returns proper ExecutionResult
        if "result_hash" in data:
            return data

        # If wrapped response
        if "result" in data and isinstance(data["result"], dict):
            result = data["result"]

            # propagate result_hash if present
            if "result_hash" in result:
                return result

            # fallback: compute deterministic hash
            return {
                **result,
                "result_hash": self._fallback_hash(result)
            }

        # fallback: treat entire payload as result
        return {
            **data,
            "result_hash": self._fallback_hash(data)
        }

    # -----------------------------------------------------------------
    # FALLBACK HASHING
    # -----------------------------------------------------------------

    def _fallback_hash(self, data: Dict[str, Any]) -> str:
        return hashlib.sha256(
            self._canonical_json(data).encode()
        ).hexdigest()

    # -----------------------------------------------------------------
    # HEALTH CHECK
    # -----------------------------------------------------------------

    def health(self) -> bool:
        """
        Check if node is reachable
        """

        try:
            response = requests.get(
                f"{self.base_url}/health",
                timeout=self.timeout
            )
            return response.status_code == 200
        except Exception:
            return False

    # -----------------------------------------------------------------
    # INFO
    # -----------------------------------------------------------------

    def info(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "base_url": self.base_url,
            "timeout": self.timeout,
            "retries": self.retries,
        }

    # -----------------------------------------------------------------
    # STRING REPRESENTATION
    # -----------------------------------------------------------------

    def __repr__(self):
        return f"<HttpNodeClient {self.node_id} @ {self.base_url}>"
