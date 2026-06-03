from __future__ import annotations

import asyncio
from typing import List, Dict, Any, Optional

from afritech.distributed.p2p.node import P2PNode
from afritech.network.server import NodeServer
from afritech.network.client import PeerClient


class NetworkNode:
    """
    Real network node combining:
    - P2P logic (gossip + execution)
    - WebSocket server (incoming)
    - WebSocket clients (outgoing peers)
    """

    def __init__(
        self,
        node_id: str,
        host: str = "localhost",
        port: int = 8765,
    ) -> None:

        self.node_id: str = node_id

        # ✅ Core P2P node
        self.p2p_node: P2PNode = P2PNode(node_id)

        # ✅ Server (incoming connections)
        self.server: NodeServer = NodeServer(
            self.p2p_node,
            host=host,
            port=port,
        )

        # ✅ Outgoing peers
        self.peers: List[PeerClient] = []

        # ✅ State
        self._running: bool = False

    # -----------------------------------------------------
    # Start node
    # -----------------------------------------------------

    async def start(self) -> None:
        """
        Start the node server.
        """

        if self._running:
            return

        self._running = True

        # ✅ run server in background
        asyncio.create_task(self.server.start())

        print(f"✅ NetworkNode '{self.node_id}' started")

    # -----------------------------------------------------
    # Stop node
    # -----------------------------------------------------

    async def stop(self) -> None:
        """
        Graceful shutdown.
        """

        if not self._running:
            return

        self._running = False

        # ✅ stop server
        await self.server.stop()

        # ✅ close all peer connections
        await asyncio.gather(
            *(peer.disconnect() for peer in self.peers),
            return_exceptions=True,
        )

        self.peers.clear()

    # -----------------------------------------------------
    # Connect to peer
    # -----------------------------------------------------

    async def connect_to_peer(self, uri: str) -> None:
        """
        Connect to another node.
        """

        client = PeerClient(uri)

        try:
            await client.connect()
        except Exception:
            return

        # ✅ message handler
        async def handler(message: Dict[str, Any]) -> None:
            try:
                self.p2p_node.receive(message)
            except Exception:
                pass

        # ✅ run receive loop in background
        asyncio.create_task(client.receive_loop(handler))

        self.peers.append(client)

        print(f"🔗 Connected to peer: {uri}")

    # -----------------------------------------------------
    # Broadcast message
    # -----------------------------------------------------

    async def broadcast(self, message: Dict[str, Any]) -> None:
        """
        Broadcast message to:
        - local P2P network
        - connected WebSocket peers
        """

        # ✅ inject into local gossip layer
        self.p2p_node.gossip.broadcast(message)

        # ✅ send to remote peers
        await asyncio.gather(
            *(peer.send(message) for peer in self.peers),
            return_exceptions=True,
        )

    # -----------------------------------------------------
    # Peer management
    # -----------------------------------------------------

    def get_peer_uris(self) -> List[str]:
        """
        Return connected peer URIs.
        """
        return [peer.uri for peer in self.peers]

    def get_node_id(self) -> str:
        return self.node_id

    # -----------------------------------------------------
    # Execution entrypoint (network-wide)
    # -----------------------------------------------------

    def execute(self, fn, epoch_snapshot) -> None:
        """
        Trigger distributed execution.

        Injects execution into the network.
        """

        self.p2p_node.execute(fn, epoch_snapshot)
