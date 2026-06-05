from __future__ import annotations

import asyncio
import json
import ssl
from typing import Any, Dict, Callable, Optional

import websockets

from afritech.network.handshake import create_handshake
from afritech.distributed.crypto import NodeIdentity
from afritech.distributed.contracts.p2p_interface import GossipMessage
from afritech.distributed.p2p.message import message_from_dict, message_to_dict


class PeerClient:
    """
    🔐 GA-Elite Secure Peer Client (WSS + Zero-Trust)

    Responsibilities:
    - Secure outbound TLS connection (WSS)
    - Signed handshake (identity proof)
    - Safe message transmission
    - Deterministic message decoding
    - Auto-reconnect with backoff
    - Failure isolation
    """

    # =====================================================
    # ✅ INIT
    # =====================================================

    def __init__(
        self,
        uri: str,
        ssl_context: Optional[ssl.SSLContext] = None,
    ) -> None:
        if not isinstance(uri, str):
            raise TypeError("uri must be a string")

        self.uri: str = uri
        self.websocket: Optional[Any] = None

        # ✅ Security (identity)
        self.identity = NodeIdentity()

        # ✅ TLS client context
        self.ssl_context = ssl_context or ssl.create_default_context()

        # ✅ State
        self._connected: bool = False
        self._running: bool = False

        # ✅ internal sync
        self._lock = asyncio.Lock()

    # =====================================================
    # ✅ CONNECT (SECURE)
    # =====================================================

    async def connect(self) -> None:
        """
        Establish secure WSS connection + handshake.
        """

        async with self._lock:
            if self._connected:
                return

            try:
                # ✅ TLS connection
                ssl_arg = self.ssl_context if self.uri.startswith("wss://") else None

                self.websocket = await websockets.connect(
                    self.uri,
                    ssl=ssl_arg,
                    ping_interval=20,
                    ping_timeout=20,
                )

                # ✅ Send signed handshake (zero-trust)
                handshake = create_handshake(self.identity)

                await self.websocket.send(
                    json.dumps(
                        handshake,
                        separators=(",", ":"),
                        sort_keys=True,
                    )
                )

                self._connected = True

            except Exception as e:
                self._connected = False
                self.websocket = None
                raise RuntimeError(f"Secure connection failed: {e}") from e

    # =====================================================
    # ✅ SEND MESSAGE
    # =====================================================

    async def send(self, message: GossipMessage | Dict[str, Any]) -> None:
        """
        Send message to peer (fail-safe).
        """

        if not self._connected or self.websocket is None:
            return

        try:
            wire_message = (
                message_to_dict(message)
                if isinstance(message, GossipMessage)
                else message
            )

            payload = json.dumps(
                wire_message,
                separators=(",", ":"),
                sort_keys=True,
                default=str,
            )

            await self.websocket.send(payload)

        except Exception:
            # ✅ fail-safe disconnect
            self._connected = False

    # =====================================================
    # ✅ RECEIVE LOOP
    # =====================================================

    async def receive_loop(
        self,
        handler: Callable[[GossipMessage], Any],
    ) -> None:
        """
        Receive messages and dispatch safely.
        """

        if self.websocket is None:
            raise RuntimeError("WebSocket not connected")

        try:
            async for raw_msg in self.websocket:

                try:
                    data: Dict[str, Any] = json.loads(raw_msg)
                    message = message_from_dict(data)
                except json.JSONDecodeError:
                    continue
                except Exception:
                    continue

                try:
                    result = handler(message)

                    if asyncio.iscoroutine(result):
                        await result

                except Exception:
                    continue

        except websockets.exceptions.ConnectionClosed:
            self._connected = False

        finally:
            self._connected = False

    # =====================================================
    # ✅ RUN (ONE-SHOT)
    # =====================================================

    async def run(
        self,
        handler: Callable[[GossipMessage], Any],
    ) -> None:

        await self.connect()
        await self.receive_loop(handler)

    # =====================================================
    # ✅ AUTO-RECONNECT LOOP
    # =====================================================

    async def run_with_reconnect(
        self,
        handler: Callable[[GossipMessage], Any],
        retry_delay: float = 2.0,
        max_backoff: float = 30.0,
    ) -> None:
        """
        Persistent secure connection with backoff.
        """

        self._running = True

        delay = retry_delay

        while self._running:
            try:
                await self.connect()
                await self.receive_loop(handler)

                # ✅ reset delay after success
                delay = retry_delay

            except Exception:
                self._connected = False
                await asyncio.sleep(delay)

                # ✅ exponential backoff
                delay = min(delay * 2, max_backoff)

    # =====================================================
    # ✅ DISCONNECT
    # =====================================================

    async def disconnect(self) -> None:
        """
        Graceful shutdown.
        """

        self._running = False

        if self.websocket is not None:
            try:
                await self.websocket.close()
            except Exception:
                pass

        self.websocket = None
        self._connected = False

    # =====================================================
    # ✅ STATE
    # =====================================================

    def is_connected(self) -> bool:
        return self._connected

    def is_running(self) -> bool:
        return self._running
