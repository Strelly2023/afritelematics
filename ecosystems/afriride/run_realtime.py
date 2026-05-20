import asyncio

import asyncio

from afritech.core.infrastructure.stream.event_stream import EventStream
from afritech.core.infrastructure.websocket.ws_server import WebSocketServer
from afritech.core.infrastructure.stream.streaming_event_store import StreamingEventStore
from afritech.core.infrastructure.stream.event_stream_bridge import EventStreamBridge




async def main():

    # ------------------------------------------------
    # CREATE EVENT STREAM
    # ------------------------------------------------
    event_stream = EventStream()

    # ------------------------------------------------
    # CREATE WS SERVER
    # ------------------------------------------------
    websocket_server = WebSocketServer()

    # ------------------------------------------------
    # CONNECT STREAM -> WS
    # ------------------------------------------------
    EventStreamBridge(
        event_stream,
        websocket_server
    )

    # ------------------------------------------------
    # CREATE STREAMING STORE
    # ------------------------------------------------
    store = StreamingEventStore(
        event_stream
    )

    # ------------------------------------------------
    # START WS SERVER
    # ------------------------------------------------
    server = await websocket_server.start()

    print("✅ WebSocket server running")
    print("✅ WebSocket running on ws://localhost:8765")

    #print("ws://localhost:8765")

    # ------------------------------------------------
    # KEEP SERVER ALIVE
    # ------------------------------------------------
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())