# ecosystems/core/infrastructure/stream/event_stream_bridge.py

import asyncio
from typing import Any, Callable


class EventStreamBridge:
    """
    Bridges EventStream → WebSocket (or any async transport).

    Responsibilities:
    - Subscribe to EventStream
    - Transform events if needed
    - Push to async broadcaster
    - Maintain non-blocking behavior

    Guarantees:
    - Does NOT mutate events
    - Does NOT store state
    - Fire-and-forget delivery model
    """

    def __init__(
        self,
        event_stream,
        websocket_server: Any,
        transformer: Callable[[dict], dict] | None = None,
    ):
        """
        event_stream: EventStream instance
        websocket_server: async broadcaster (must expose broadcast())
        transformer: optional event mapping function
        """

        self.event_stream = event_stream
        self.websocket_server = websocket_server
        self.transformer = transformer

        # register subscriber immediately
        self.event_stream.subscribe(self.handle_event)

    # --------------------------------------------------
    # EVENT HANDLER (SYNC ENTRY POINT)
    # --------------------------------------------------
    def handle_event(self, event: dict):
        """
        Called by EventStream (sync context).
        Schedules async broadcast safely.
        """

        try:
            # optional transformation step
            payload = (
                self.transformer(event)
                if self.transformer
                else event
            )

            # schedule async delivery
            asyncio.create_task(
                self._dispatch(payload)
            )

        except Exception as e:
            print(f"[Bridge] handle_event error: {e}")

    # --------------------------------------------------
    # ASYNC DISPATCH
    # --------------------------------------------------
    async def _dispatch(self, payload: dict):
        """
        Actual async broadcast execution.
        """

        try:
            await self.websocket_server.broadcast(payload)

        except Exception as e:
            print(f"[Bridge] dispatch error: {e}")

    # --------------------------------------------------
    # MANUAL DISPATCH (FOR TESTING)
    # --------------------------------------------------
    async def dispatch_now(self, event: dict):
        """
        Direct async send (bypasses stream).
        Useful for tests.
        """

        await self._dispatch(event)

    # --------------------------------------------------
    # UNSUBSCRIBE / SHUTDOWN
    # --------------------------------------------------
    def close(self):
        """
        Detach bridge from stream.
        """

        self.event_stream.unsubscribe(self.handle_event)

    # --------------------------------------------------
    # DEBUG SNAPSHOT
    # --------------------------------------------------
    def snapshot(self):
        """
        Lightweight diagnostics.
        """

        return {
            "stream_subscribed": True,
            "transformer_enabled": self.transformer is not None,
            "websocket_server": repr(self.websocket_server),
        }