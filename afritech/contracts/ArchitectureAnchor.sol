// SPDX-License-Identifier: MIT
// afritech/contracts/ArchitectureAnchor.sol

pragma solidity ^0.8.20;

contract ArchitectureAnchor {

    // =========================
    // ✅ DATA STRUCTURE
    // =========================

    struct AnchorRecord {
        bytes32 proofHash;
        address publisher;
        uint256 timestamp;
        bool exists;
    }

    // =========================
    // ✅ STATE
    // =========================

    address public immutable owner;

    // anchorId => record
    mapping(string => AnchorRecord) private anchors;

    // =========================
    // ✅ EVENTS
    // =========================

    event ProofAnchored(
        string anchorId,
        bytes32 indexed proofHash,
        address indexed publisher,
        uint256 timestamp
    );

    event OwnershipTransferred(
        address indexed previousOwner,
        address indexed newOwner
    );

    // =========================
    // ✅ ERRORS (CHEAPER THAN REQUIRE)
    // =========================

    error AnchorAlreadyExists(string anchorId);
    error AnchorNotFound(string anchorId);
    error Unauthorized();

    // =========================
    // ✅ CONSTRUCTOR
    // =========================

    constructor() {
        owner = msg.sender;
    }

    // =========================
    // ✅ MODIFIERS
    // =========================

    modifier onlyOwner() {
        if (msg.sender != owner) revert Unauthorized();
        _;
    }

    // =========================
    // ✅ CORE WRITE FUNCTION
    // =========================

    function anchorProof(
        string calldata anchorId,
        bytes32 proofHash
    ) external {
        if (anchors[anchorId].exists) {
            revert AnchorAlreadyExists(anchorId);
        }

        anchors[anchorId] = AnchorRecord({
            proofHash: proofHash,
            publisher: msg.sender,
            timestamp: block.timestamp,
            exists: true
        });

        emit ProofAnchored(
            anchorId,
            proofHash,
            msg.sender,
            block.timestamp
        );
    }

    // =========================
    // ✅ OPTIONAL: RESTRICTED VERSION (ELITE CONTROL)
    // =========================
    // Use THIS instead if you want only backend to anchor proofs

    function anchorProofRestricted(
        string calldata anchorId,
        bytes32 proofHash
    ) external onlyOwner {

        if (anchors[anchorId].exists) {
            revert AnchorAlreadyExists(anchorId);
        }

        anchors[anchorId] = AnchorRecord({
            proofHash: proofHash,
            publisher: msg.sender,
            timestamp: block.timestamp,
            exists: true
        });

        emit ProofAnchored(
            anchorId,
            proofHash,
            msg.sender,
            block.timestamp
        );
    }

    // =========================
    // ✅ VERIFICATION
    // =========================

    function verifyAnchor(
        string calldata anchorId,
        bytes32 expectedProofHash
    ) external view returns (bool) {

        AnchorRecord storage record = anchors[anchorId];

        if (!record.exists) {
            return false;
        }

        return record.proofHash == expectedProofHash;
    }

    // =========================
    // ✅ READ FUNCTIONS
    // =========================

    function getAnchor(
        string calldata anchorId
    )
        external
        view
        returns (
            bytes32 proofHash,
            address publisher,
            uint256 timestamp
        )
    {
        AnchorRecord storage record = anchors[anchorId];

        if (!record.exists) {
            revert AnchorNotFound(anchorId);
        }

        return (
            record.proofHash,
            record.publisher,
            record.timestamp
        );
    }

    function anchorExists(
        string calldata anchorId
    ) external view returns (bool) {
        return anchors[anchorId].exists;
    }

    function anchorPublisher(
        string calldata anchorId
    ) external view returns (address) {

        AnchorRecord storage record = anchors[anchorId];

        if (!record.exists) {
            revert AnchorNotFound(anchorId);
        }

        return record.publisher;
    }

    function anchorTimestamp(
        string calldata anchorId
    ) external view returns (uint256) {

        AnchorRecord storage record = anchors[anchorId];

        if (!record.exists) {
            revert AnchorNotFound(anchorId);
        }

        return record.timestamp;
    }
}
