// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract NovaTrustLightVerifier {
    struct ReceiptAnchor {
        bytes32 receiptHash;
        bytes32 bridgeHash;
        bytes32 stateRoot;
        uint256 blockHeight;
        bool verified;
    }

    mapping(bytes32 => ReceiptAnchor) private anchors;

    event ReceiptAnchored(
        bytes32 indexed receiptHash,
        bytes32 indexed bridgeHash,
        bytes32 stateRoot,
        uint256 blockHeight
    );

    function anchorReceipt(
        bytes32 receiptHash,
        bytes32 bridgeHash,
        bytes32 stateRoot,
        uint256 blockHeight
    ) external returns (bool) {
        require(receiptHash != bytes32(0), "receipt_required");
        require(bridgeHash != bytes32(0), "bridge_required");
        require(stateRoot != bytes32(0), "state_root_required");

        anchors[receiptHash] = ReceiptAnchor({
            receiptHash: receiptHash,
            bridgeHash: bridgeHash,
            stateRoot: stateRoot,
            blockHeight: blockHeight,
            verified: true
        });

        emit ReceiptAnchored(receiptHash, bridgeHash, stateRoot, blockHeight);
        return true;
    }

    function isAnchored(bytes32 receiptHash) external view returns (bool) {
        return anchors[receiptHash].verified;
    }
}
