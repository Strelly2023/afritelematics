from __future__ import annotations

import asyncio
import json
import os
import ssl
import time
import websockets

from typing import Set, Dict, Any, Optional

from afritech.distributed.p2p.node import P2PNode
from afritech.distributed.contracts.p2p_interface import GossipMessage
from afritech.distributed.p2p.message import (
    message_from_dict,
    message_to_dict,
    validate_message_structure,
)
from afritech.network.handshake import verify_handshake
from afritech.network.rate_limit import RateLimiter


class NodeServer:
    """
    🔐 GA-Elite TLS + Zero-Trust WebSocket server

    Responsibilities:
    - Secure WSS transport
    - Signed handshake verification
    - Replay protection (nonce + timestamp)
    - Rate limiting (DoS protection)
    - Message validation + forwarding
    - Safe connection lifecycle
    """

    # =====================================================
    # ✅ INIT
    # =====================================================

    def __init__(
        self,
        node: P2PNode,
        host: str = "localhost",
        port: int = 8765,
        certfile: Optional[str] = "server.crt",
        keyfile: Optional[str] = "server.key",
        ssl_context: Optional[ssl.SSLContext] = None,
        require_tls: bool = False,
    ) -> None:

        if not isinstance(node, P2PNode):
            raise TypeError("node must be a P2PNode")

        self.node: P2PNode = node
        self.host = host
        self.port = port

        # ✅ TLS configuration (WSS when certificates/context are present)
        self.ssl_context = ssl_context or self._build_ssl_context(
            certfile,
            keyfile,
            require_tls,
        )

        # ✅ Active connections
        self.connections: Set[Any] = set()

        # ✅ Peer identities
        self.peer_ids: Dict[Any, str] = {}

        # ✅ Rate limiter
        self.rate_limiter = RateLimiter()

        # ✅ Replay protection (nonce cache)
        self._seen_nonces: Dict[str, int] = {}
        self._nonce_ttl: int = 60  # seconds

        self._server: Optional[Any] = None
        self._running: bool = False

    # =====================================================
    # ✅ NONCE PROTECTION (GA-ELITE)
    # =====================================================

    def _cleanup_nonces(self) -> None:
        """
        Remove expired nonces (prevents memory growth).
        """
        now = int(time.time())

        expired = [
            nonce for nonce, ts in self._seen_nonces.items()
            if now - ts > self._nonce_ttl
        ]

        for nonce in expired:
            del self._seen_nonces[nonce]

    def _validate_nonce(self, nonce: Any, timestamp: Any) -> bool:
        """
        Prevent replay attacks using nonce + timestamp.
        """

        if not isinstance(nonce, str):
            return False

        if not isinstance(timestamp, int):
            return False

        self._cleanup_nonces()

        now = int(time.time())

        # ✅ timestamp validity
        if abs(now - timestamp) > self._nonce_ttl:
            return False

        # ✅ replay protection
        if nonce in self._seen_nonces:
            return False

        # ✅ store nonce
        self._seen_nonces[nonce] = timestamp

        return True

    # =====================================================
    # ✅ CONNECTION HANDLER
    # =====================================================

    async def handler(self, websocket: Any) -> None:
        """
        Secure connection lifecycle.
        """

        try:
            # -------------------------------------------------
            # ✅ STEP 1 — HANDSHAKE
            # -------------------------------------------------

            raw = await websocket.recv()

            try:
                handshake = json.loads(raw)
            except Exception:
                await websocket.close()
                return

            if not verify_handshake(handshake):
                await websocket.close()
                return

            peer_id = handshake.get("node_id")
            nonce = handshake.get("nonce")
            timestamp = handshake.get("timestamp")

            # -------------------------------------------------
            # ✅ STEP 2 — NONCE VALIDATION (NEW)
            # -------------------------------------------------

            if not self._validate_nonce(nonce, timestamp):
                await websocket.close()
                return

            # -------------------------------------------------
            # ✅ STEP 3 — RATE LIMIT
            # -------------------------------------------------

            if not self.rate_limiter.allow(peer_id):
                await websocket.close()
                return

            # -------------------------------------------------
            # ✅ ACCEPT CONNECTION
            # -------------------------------------------------

            self.connections.add(websocket)
            self.peer_ids[websocket] = peer_id

            print(f"✅ Secure peer connected: {peer_id}")

            # -------------------------------------------------
            # ✅ MESSAGE LOOP
            # -------------------------------------------------

            async for raw_message in websocket:

                try:
                    data: Dict[str, Any] = json.loads(raw_message)
                except json.JSONDecodeError:
                    continue

                try:
                    message = message_from_dict(data)
                except Exception:
                    continue

                try:
                    result = self.node.receive_message(message)

                    if asyncio.iscoroutine(result):
                        await result

                except Exception:
                    continue

        except websockets.exceptions.ConnectionClosed:
            pass

        finally:
            self.connections.discard(websocket)
            self.peer_ids.pop(websocket, None)

    # =====================================================
    # ✅ START SERVER (TLS ENABLED)
    # =====================================================

    async def start(self) -> None:

        if self._running:
            return

        self._server = await websockets.serve(
            self.handler,
            self.host,
            self.port,
            ssl=self.ssl_context,
            ping_interval=20,
            ping_timeout=20,
        )

        self._running = True

        scheme = "wss" if self.ssl_context is not None else "ws"
        print(f"🌐 Secure node running at {scheme}://{self.host}:{self.port}")

        await self._wait_until_closed()

    async def _wait_until_closed(self) -> None:
        if self._server is None:
            return

        try:
            await self._server.wait_closed()
        except Exception:
            pass

    # =====================================================
    # ✅ STOP SERVER
    # =====================================================

    async def stop(self) -> None:

        if not self._running:
            return

        self._running = False

        if self._server is not None:
            try:
                self._server.close()
                await self._server.wait_closed()
            except Exception:
                pass

        await asyncio.gather(
            *(self._safe_close(conn) for conn in list(self.connections)),
            return_exceptions=True,
        )

        self.connections.clear()
        self.peer_ids.clear()
        self._seen_nonces.clear()

    async def _safe_close(self, conn: Any) -> None:
        try:
            await conn.close()
        except Exception:
            pass

    # =====================================================
    # ✅ BROADCAST
    # =====================================================

    async def broadcast(self, message: GossipMessage | Dict[str, Any]) -> None:

        if not self.connections:
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
        except Exception:
            return

        dead: Set[Any] = set()

        await asyncio.gather(
            *(self._send_safe(conn, payload, dead) for conn in self.connections),
            return_exceptions=True,
        )

        for conn in dead:
            self.connections.discard(conn)
            self.peer_ids.pop(conn, None)

    async def _send_safe(
        self,
        conn: Any,
        payload: str,
        dead: Set[Any],
    ) -> None:
        try:
            await conn.send(payload)
        except Exception:
            dead.add(conn)

    # =====================================================
    # ✅ LOCAL INJECTION
    # =====================================================

    def inject(self, message: GossipMessage | Dict[str, Any]) -> None:

        try:
            gossip_message = (
                message
                if isinstance(message, GossipMessage)
                else message_from_dict(message)
            )
        except Exception:
            return

        if not validate_message_structure(gossip_message):
            return

        try:
            result = self.node.receive_message(gossip_message)

            if asyncio.iscoroutine(result):
                asyncio.create_task(result)

        except Exception:
            pass

    # =====================================================
    # ✅ STATE
    # =====================================================

    def is_running(self) -> bool:
        return self._running

    def _build_ssl_context(
        self,
        certfile: Optional[str],
        keyfile: Optional[str],
        require_tls: bool,
    ) -> Optional[ssl.SSLContext]:
        if certfile and keyfile and os.path.exists(certfile) and os.path.exists(keyfile):
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(certfile=certfile, keyfile=keyfile)
            return context

        if require_tls:
            raise FileNotFoundError("TLS certificate and key are required")

        return None
