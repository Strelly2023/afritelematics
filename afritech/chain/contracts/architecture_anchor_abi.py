# afritech/chain/contracts/architecture_anchor_abi.py

ARCHITECTURE_ANCHOR_ABI = [

    # =========================
    # ✅ CONSTRUCTOR
    # =========================
    {
        "inputs": [],
        "stateMutability": "nonpayable",
        "type": "constructor"
    },

    # =========================
    # ✅ EVENTS
    # =========================
    {
        "anonymous": False,
        "inputs": [
            {"indexed": False, "internalType": "string", "name": "anchorId", "type": "string"},
            {"indexed": True, "internalType": "bytes32", "name": "proofHash", "type": "bytes32"},
            {"indexed": True, "internalType": "address", "name": "publisher", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "timestamp", "type": "uint256"},
        ],
        "name": "ProofAnchored",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "previousOwner", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "newOwner", "type": "address"},
        ],
        "name": "OwnershipTransferred",
        "type": "event",
    },

    # =========================
    # ✅ WRITE FUNCTIONS
    # =========================
    {
        "inputs": [
            {"internalType": "string", "name": "anchorId", "type": "string"},
            {"internalType": "bytes32", "name": "proofHash", "type": "bytes32"},
        ],
        "name": "anchorProof",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "string", "name": "anchorId", "type": "string"},
            {"internalType": "bytes32", "name": "proofHash", "type": "bytes32"},
        ],
        "name": "anchorProofRestricted",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },

    # =========================
    # ✅ VERIFICATION
    # =========================
    {
        "inputs": [
            {"internalType": "string", "name": "anchorId", "type": "string"},
            {"internalType": "bytes32", "name": "expectedProofHash", "type": "bytes32"},
        ],
        "name": "verifyAnchor",
        "outputs": [
            {"internalType": "bool", "name": "", "type": "bool"}
        ],
        "stateMutability": "view",
        "type": "function",
    },

    # =========================
    # ✅ READ FUNCTIONS
    # =========================
    {
        "inputs": [
            {"internalType": "string", "name": "anchorId", "type": "string"}
        ],
        "name": "getAnchor",
        "outputs": [
            {"internalType": "bytes32", "name": "proofHash", "type": "bytes32"},
            {"internalType": "address", "name": "publisher", "type": "address"},
            {"internalType": "uint256", "name": "timestamp", "type": "uint256"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "string", "name": "anchorId", "type": "string"}
        ],
        "name": "anchorExists",
        "outputs": [
            {"internalType": "bool", "name": "", "type": "bool"}
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "string", "name": "anchorId", "type": "string"}
        ],
        "name": "anchorPublisher",
        "outputs": [
            {"internalType": "address", "name": "", "type": "address"}
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "string", "name": "anchorId", "type": "string"}
        ],
        "name": "anchorTimestamp",
        "outputs": [
            {"internalType": "uint256", "name": "", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function",
    },

    # =========================
    # ✅ OWNER
    # =========================
    {
        "inputs": [],
        "name": "owner",
        "outputs": [
            {"internalType": "address", "name": "", "type": "address"}
        ],
        "stateMutability": "view",
        "type": "function",
    },
]