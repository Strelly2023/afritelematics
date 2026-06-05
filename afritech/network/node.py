from __future__ import annotations

import asyncio
from typing import List, Dict, Any, Optional, Callable

from afritech.distributed.p2p.node import P2PNode
from afritech.network.server import NodeServer
from afritech.network.client import PeerClient
from afritech.distributed.contracts.p2p_interface import GossipMessage


class NetworkNode:
    """
    Real network node combining:
    - P2P logic (gossip + execution)
    - WebSocket server (incoming)
    - WebSocket clients (outgoing peers)

    GA Elite guarantees:
    - Deterministic execution injection
    - Replay-safe propagation
    - Fail-safe networking
    """

    # =====================================================
    # ✅ INIT
    # =====================================================

    def __init__(
        self,
        node_id: str,
        host: str = "localhost",
        port: int = 8765,
        certfile: Optional[str] = "server.crt",
        keyfile: Optional[str] = "server.key",
        require_tls: bool = False,
    ) -> None:

        if not isinstance(node_id, str):
            raise TypeError("node_id must be a string")

        self.node_id: str = node_id

        # ✅ Core P2P node
        self.p2p_node: P2PNode = P2PNode(node_id)

        # ✅ Server (incoming connections)
        self.server: NodeServer = NodeServer(
            self.p2p_node,
            host=host,
            port=port,
            certfile=certfile,
            keyfile=keyfile,
            require_tls=require_tls,
        )

        # ✅ Outgoing peers
        self.peers: List[PeerClient] = []

        # ✅ Runtime state
        self._running: bool = False

    # =====================================================
    # ✅ START NODE
    # =====================================================

    async def start(self) -> None:
        """
        Start the node server.
        """

        if self._running:
            return

        self._running = True

        # ✅ Run server in background
        asyncio.create_task(self.server.start())

        print(f"✅ NetworkNode '{self.node_id}' started")

    # =====================================================
    # ✅ STOP NODE
    # =====================================================

    async def stop(self) -> None:
        """
        Graceful shutdown.
        """

        if not self._running:
            return

        self._running = False

        # ✅ Stop server
        await self.server.stop()

        # ✅ Close all peer connections
        await asyncio.gather(
            *(peer.disconnect() for peer in self.peers),
            return_exceptions=True,
        )

        self.peers.clear()

        print(f"🛑 NetworkNode '{self.node_id}' stopped")

    # =====================================================
    # ✅ CONNECT TO PEER
    # =====================================================

    async def connect_to_peer(self, uri: str) -> None:
        """
        Connect to another node.
        """

        if not isinstance(uri, str):
            return

        client = PeerClient(uri)

        try:
            await client.connect()
        except Exception:
            return

        # ✅ Handler MUST accept GossipMessage (IMPORTANT FIX)
        async def handler(message: GossipMessage) -> None:
            try:
                self.p2p_node.receive_message(message)
            except Exception:
                pass  # fail-safe

        # ✅ Run receive loop in background
        asyncio.create_task(client.receive_loop(handler))

        self.peers.append(client)

        print(f"🔗 Connected to peer: {uri}")

    # =====================================================
    # ✅ BROADCAST
    # =====================================================

    async def broadcast(self, message: GossipMessage) -> None:
        """
        Broadcast message to:
        - local P2P network
        - connected WebSocket peers
        """

        if message is None:
            return

        try:
            # ✅ Inject into local gossip layer
            self.p2p_node.receive_message(message)

            # ✅ Send to remote peers
            await asyncio.gather(
                *(peer.send(message) for peer in self.peers),
                return_exceptions=True,
            )

        except Exception:
            pass  # fail-safe

    # =====================================================
    # ✅ PEER MANAGEMENT
    # =====================================================

    def get_peer_uris(self) -> List[str]:
        return [peer.uri for peer in self.peers]

    def get_node_id(self) -> str:
        return self.node_id

    def register_function(self, fn_id: str, fn: Callable) -> None:
        self.p2p_node.register_function(fn_id, fn)

    # =====================================================
    # ✅ EXECUTION ENTRYPOINT (NETWORK-WIDE)
    # =====================================================

    def execute(
        self,
        fn: Callable | str,
        epoch_snapshot,
        args: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Trigger distributed execution.

        Injects execution into:
        - local node
        - gossip propagation
        - remote peers
        """

        try:
            if callable(fn):
                fn_id = f"{getattr(fn, '__module__', 'unknown')}.{getattr(fn, '__name__', 'anonymous')}"
                self.register_function(fn_id, fn)
            else:
                fn_id = fn

            message = self.p2p_node.execute(fn_id, epoch_snapshot, args)

            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                return

            loop.create_task(self._broadcast_to_remote_peers(message))
        except Exception:
            pass  # fail-safe

    async def _broadcast_to_remote_peers(self, message: GossipMessage) -> None:
        await asyncio.gather(
            *(peer.send(message) for peer in self.peers),
            return_exceptions=True,
        )
