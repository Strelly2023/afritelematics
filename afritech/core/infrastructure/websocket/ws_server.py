import asyncio
import json
import websockets


class WebSocketServer:

    def __init__(self):
        self.clients = set()

    # --------------------------------------------
    # CLIENT HANDLER
    # --------------------------------------------
    async def handler(self, websocket):

        self.clients.add(websocket)

        try:
            async for _ in websocket:
                pass

        finally:
            self.clients.remove(websocket)

    # --------------------------------------------
    # BROADCAST
    # --------------------------------------------
    async def broadcast(self, message):

        if not self.clients:
            return

        payload = json.dumps(message)

        await asyncio.gather(
            *(client.send(payload) for client in self.clients)
        )

    # --------------------------------------------
    # START SERVER
    # --------------------------------------------
    async def start(self, host="localhost", port=8765):

        return await websockets.serve(
            self.handler,
            host,
            port
        )