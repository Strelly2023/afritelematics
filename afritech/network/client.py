from __future__ import annotations

import asyncio
import json
import websockets

from typing import Any, Dict, Callable, Optional


class PeerClient:
    """
    Connects to another node via WebSocket.

    Responsibilities:
    - Establish outbound connections
    - Send messages safely
    - Receive and dispatch incoming messages
    - Handle reconnect logic
    - Maintain deterministic-safe communication

    Notes:
    - Uses stable typing (Any) to avoid websockets version issues
    - Fully isolated error boundaries
    """

    def __init__(self, uri: str) -> None:
        if not isinstance(uri, str):
            raise TypeError("uri must be a string")

        self.uri: str = uri
        self.websocket: Optional[Any] = None  # ✅ version-safe
        self._connected: bool = False

        # ✅ internal lifecycle
        self._running: bool = False
        self._lock = asyncio.Lock()

    # -----------------------------------------------------
    # Connect
    # -----------------------------------------------------

    async def connect(self) -> None:
        """
        Establish connection to peer.
        """

        async with self._lock:
            if self._connected:
                return

            try:
                self.websocket = await websockets.connect(
                    self.uri,
                    ping_interval=20,
                    ping_timeout=20,
                )

                self._connected = True

            except Exception as e:
                self._connected = False
                raise RuntimeError(f"Connection failed: {e}") from e

    # -----------------------------------------------------
    # Send message
    # -----------------------------------------------------

    async def send(self, message: Dict[str, Any]) -> None:
        """
        Send message to peer (non-blocking safe).
        """

        if not self._connected or self.websocket is None:
            return

        try:
            # ✅ deterministic encoding (matches distributed system rules)
            payload = json.dumps(
                message,
                separators=(",", ":"),
                sort_keys=True,
                default=str,
            )

            await self.websocket.send(payload)

        except Exception:
            # ✅ fail-safe disconnect
            self._connected = False

    # -----------------------------------------------------
    # Receive loop
    # -----------------------------------------------------

    async def receive_loop(
        self,
        handler: Callable[[Dict[str, Any]], Any],
    ) -> None:
        """
        Continuously receive messages and dispatch handler.
        """

        if self.websocket is None:
            raise RuntimeError("WebSocket not connected")

        try:
            async for raw_msg in self.websocket:

                # ✅ safe JSON decode
                try:
                    data: Dict[str, Any] = json.loads(raw_msg)
                except json.JSONDecodeError:
                    continue

                # ✅ handler isolation
                try:
                    result = handler(data)

                    if asyncio.iscoroutine(result):
                        await result

                except Exception:
                    continue

        except websockets.exceptions.ConnectionClosed:
            self._connected = False

        finally:
            self._connected = False

    # -----------------------------------------------------
    # Run loop (connect + receive)
    # -----------------------------------------------------

    async def run(
        self,
        handler: Callable[[Dict[str, Any]], Any],
    ) -> None:
        """
        Single lifecycle execution:
        connect → receive loop
        """

        await self.connect()
        await self.receive_loop(handler)

    # -----------------------------------------------------
    # Auto-reconnect loop
    # -----------------------------------------------------

    async def run_with_reconnect(
        self,
        handler: Callable[[Dict[str, Any]], Any],
        retry_delay: float = 2.0,
        max_backoff: float = 30.0,
    ) -> None:
        """
        Persistent connection with exponential backoff.
        """

        self._running = True
        delay = retry_delay

        while self._running:
            try:
                await self.connect()
                await self.receive_loop(handler)

                # reset delay on success
                delay = retry_delay

            except Exception:
                self._connected = False
                await asyncio.sleep(delay)

                # ✅ exponential backoff
                delay = min(delay * 2, max_backoff)

    # -----------------------------------------------------
    # Disconnect
    # -----------------------------------------------------

    async def disconnect(self) -> None:
        """
        Gracefully close connection.
        """

        self._running = False

        if self.websocket is not None:
            try:
                await self.websocket.close()
            except Exception:
                pass

        self.websocket = None
        self._connected = False

    # -----------------------------------------------------
    # State
    # -----------------------------------------------------

    def is_connected(self) -> bool:
        return self._connected

    def is_running(self) -> bool:
        return self._running
