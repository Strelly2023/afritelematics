// SPDX-License-Identifier: MIT
// afritech/contracts/ArchitectureAnchorV2.sol

pragma solidity ^0.8.20;

contract ArchitectureAnchorV2 {
    struct AnchorRecord {
        bytes32 proofHash;
        address publisher;
        uint256 timestamp;
        bytes32 context;
        bool exists;
    }

    address public immutable owner;

    mapping(bytes32 => AnchorRecord) private anchors;
    mapping(bytes32 => bool) private proofUsed;

    event ProofAnchored(
        bytes32 indexed anchorId,
        bytes32 indexed proofHash,
        address indexed publisher,
        uint256 timestamp,
        bytes32 context
    );

    error AnchorAlreadyExists();
    error AnchorNotFound();
    error Unauthorized();
    error DuplicateProof();
    error ArrayLengthMismatch();
    error EmptyBatch();
    error ZeroAnchorId();
    error ZeroProofHash();

    constructor() {
        owner = msg.sender;
    }

    modifier onlyOwner() {
        if (msg.sender != owner) revert Unauthorized();
        _;
    }

    function anchorProof(
        bytes32 anchorId,
        bytes32 proofHash,
        bytes32 context,
        bool enforceUniqueProof
    ) external onlyOwner {
        _anchor(anchorId, proofHash, context, enforceUniqueProof);
    }

    function anchorBatch(
        bytes32[] calldata anchorIds,
        bytes32[] calldata proofHashes,
        bytes32[] calldata contexts,
        bool enforceUniqueProof
    ) external onlyOwner {
        uint256 length = anchorIds.length;

        if (length == 0) revert EmptyBatch();
        if (length != proofHashes.length || length != contexts.length) {
            revert ArrayLengthMismatch();
        }

        for (uint256 i = 0; i < length; i++) {
            _anchor(anchorIds[i], proofHashes[i], contexts[i], enforceUniqueProof);
        }
    }

    function verifyAnchor(
        bytes32 anchorId,
        bytes32 expectedProofHash
    ) external view returns (bool) {
        AnchorRecord storage record = anchors[anchorId];
        if (!record.exists) return false;
        return record.proofHash == expectedProofHash;
    }

    function getAnchor(
        bytes32 anchorId
    )
        external
        view
        returns (
            bytes32 proofHash,
            address publisher,
            uint256 timestamp,
            bytes32 context
        )
    {
        AnchorRecord storage record = anchors[anchorId];
        if (!record.exists) revert AnchorNotFound();

        return (
            record.proofHash,
            record.publisher,
            record.timestamp,
            record.context
        );
    }

    function anchorExists(bytes32 anchorId) external view returns (bool) {
        return anchors[anchorId].exists;
    }

    function proofHashUsed(bytes32 proofHash) external view returns (bool) {
        return proofUsed[proofHash];
    }

    function _anchor(
        bytes32 anchorId,
        bytes32 proofHash,
        bytes32 context,
        bool enforceUniqueProof
    ) private {
        if (anchorId == bytes32(0)) revert ZeroAnchorId();
        if (proofHash == bytes32(0)) revert ZeroProofHash();
        if (anchors[anchorId].exists) revert AnchorAlreadyExists();
        if (enforceUniqueProof && proofUsed[proofHash]) revert DuplicateProof();

        anchors[anchorId] = AnchorRecord({
            proofHash: proofHash,
            publisher: msg.sender,
            timestamp: block.timestamp,
            context: context,
            exists: true
        });

        if (enforceUniqueProof) {
            proofUsed[proofHash] = true;
        }

        emit ProofAnchored(
            anchorId,
            proofHash,
            msg.sender,
            block.timestamp,
            context
        );
    }
}
