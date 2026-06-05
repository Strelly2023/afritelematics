# Network

The network layer provides secure node-to-node transport and discovery.

## Components

- `afritech/network/client.py`
- `afritech/network/server.py`
- `afritech/network/handshake.py`
- `afritech/network/rate_limit.py`
- `afritech/network/discovery/`
- `afritech/network/trust/`

## Responsibilities

- Establish WebSocket or WSS connections
- Verify signed peer handshakes
- Prevent nonce replay
- Rate-limit inbound peers
- Discover peers through DHT-style routing
- Block low-trust peers through the trust firewall
