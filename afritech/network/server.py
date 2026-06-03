from __future__ import annotations

import asyncio
import json
import websockets

from typing import Set, Dict, Any, Optional

from afritech.distributed.p2p.node import P2PNode
from afritech.distributed.p2p.message import validate_message_structure


class NodeServer:
    """
    WebSocket server for a node.

    Responsibilities:
    - Accept incoming peer connections
    - Receive and validate messages
    - Forward valid messages to P2P node
    - Broadcast outbound messages
    - Manage connection lifecycle safely
    """

    def __init__(
        self,
        node: P2PNode,
        host: str = "localhost",
        port: int = 8765,
    ) -> None:

        if not isinstance(node, P2PNode):
            raise TypeError("node must be a P2PNode")

        self.node: P2PNode = node
        self.host: str = host
        self.port: int = port

        # ✅ Generic connection abstraction (stable across websockets versions)
        self.connections: Set[Any] = set()

        # ✅ runtime server instance (no brittle typing)
        self._server: Optional[Any] = None

        self._running: bool = False

    # -----------------------------------------------------
    # Connection handler
    # -----------------------------------------------------

    async def handler(self, websocket: Any) -> None:
        """
        Handle a connected peer.
        """

        self.connections.add(websocket)

        try:
            async for raw_message in websocket:

                # ✅ Safe JSON decoding
                try:
                    data: Dict[str, Any] = json.loads(raw_message)
                except json.JSONDecodeError:
                    continue

                # ✅ Structural validation (zero-trust boundary)
                if not validate_message_structure(data):
                    continue

                # ✅ Forward to P2P node (supports async & sync)
                try:
                    result = self.node.receive(data)

                    if asyncio.iscoroutine(result):
                        await result

                except Exception:
                    # isolate node-level failures
                    continue

        except websockets.exceptions.ConnectionClosed:
            pass

        finally:
            self.connections.discard(websocket)

    # -----------------------------------------------------
    # Start server
    # -----------------------------------------------------

    async def start(self) -> None:
        """
        Start WebSocket server.
        """

        if self._running:
            return

        self._server = await websockets.serve(
            self.handler,
            self.host,
            self.port,
            ping_interval=20,
            ping_timeout=20,
        )

        self._running = True

        print(f"🌐 Node running at ws://{self.host}:{self.port}")

        await self._wait_until_closed()

    async def _wait_until_closed(self) -> None:
        """
        Safe wait loop that avoids typing issues.
        """
        if self._server is None:
            return

        try:
            await self._server.wait_closed()
        except Exception:
            pass

    # -----------------------------------------------------
    # Background run
    # -----------------------------------------------------

    def run_background(self) -> asyncio.Task:
        """
        Start server as background task.
        """
        return asyncio.create_task(self.start())

    # -----------------------------------------------------
    # Stop server
    # -----------------------------------------------------

    async def stop(self) -> None:
        """
        Stop server gracefully.
        """

        if not self._running:
            return

        self._running = False

        # ✅ Close server safely
        if self._server is not None:
            try:
                self._server.close()
                await self._server.wait_closed()
            except Exception:
                pass

        # ✅ Close all active connections
        await asyncio.gather(
            *(self._safe_close(conn) for conn in list(self.connections)),
            return_exceptions=True,
        )

        self.connections.clear()

    async def _safe_close(self, conn: Any) -> None:
        try:
            await conn.close()
        except Exception:
            pass

    # -----------------------------------------------------
    # Broadcast
    # -----------------------------------------------------

    async def broadcast(self, message: Dict[str, Any]) -> None:
        """
        Send message to all connected peers.
        """

        if not self.connections:
            return

        # ✅ Deterministic serialization (important for distributed systems)
        try:
            payload = json.dumps(
                message,
                separators=(",", ":"),
                sort_keys=True,
                default=str,
            )
        except Exception:
            return

        # ✅ Concurrent broadcast (faster + scalable)
        tasks = []
        dead_connections: Set[Any] = set()

        for conn in self.connections:
            tasks.append(self._send_safe(conn, payload, dead_connections))

        await asyncio.gather(*tasks, return_exceptions=True)

        # ✅ Cleanup dead connections
        for conn in dead_connections:
            self.connections.discard(conn)

    async def _send_safe(
        self,
        conn: Any,
        payload: str,
        dead_connections: Set[Any],
    ) -> None:
        try:
            await conn.send(payload)
        except Exception:
            dead_connections.add(conn)

    # -----------------------------------------------------
    # Local injection
    # -----------------------------------------------------

    def inject(self, message: Dict[str, Any]) -> None:
        """
        Inject message directly into node (no network).
        """

        if not validate_message_structure(message):
            return

        try:
            result = self.node.receive(message)

            if asyncio.iscoroutine(result):
                asyncio.create_task(result)

        except Exception:
            pass

    # -----------------------------------------------------
    # State
    # -----------------------------------------------------

    def is_running(self) -> bool:
        return self._running
