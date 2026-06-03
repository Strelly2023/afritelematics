from __future__ import annotations

import asyncio
import signal
from typing import List

from afritech.network.node import NetworkNode
from afritech.network.discovery import load_peers, save_peer


# -----------------------------------------------------
# Main runtime
# -----------------------------------------------------

async def main() -> None:
    node_id = "node-A"
    port = 8765

    node = NetworkNode(node_id, port=port)

    print(f"🚀 Starting node: {node_id}")

    # ✅ Start server (non-blocking)
    await node.start()

    # ✅ Connect to known peers
    peers: List[str] = load_peers()

    for peer in peers:
        try:
            await node.connect_to_peer(peer)
        except Exception:
            # ✅ ignore bad peers (zero-trust principle)
            continue

    print(f"🔗 Connected to {len(node.get_peer_uris())} peers")

    # ✅ Keep running until interrupted
    stop_event = asyncio.Event()

    def shutdown():
        print("\n🛑 Shutdown signal received")
        stop_event.set()

    # ✅ Handle CTRL+C / SIGTERM
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT, shutdown)
    loop.add_signal_handler(signal.SIGTERM, shutdown)

    # ✅ Wait for shutdown signal
    await stop_event.wait()

    print("🔻 Stopping node...")

    # ✅ Graceful shutdown
    await node.stop()

    print("✅ Node stopped cleanly")


# -----------------------------------------------------
# Entry point
# -----------------------------------------------------

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Forced shutdown")
