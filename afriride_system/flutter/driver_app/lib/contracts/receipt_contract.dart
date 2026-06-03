// Canonical Receipt Evidence Contract
//
// Purpose:
// Represents completed-ride receipt evidence returned by the AfriRide API.
//
// Constitutional Properties:
// - Immutable
// - Read-only
// - Evidence-only
// - Authority-neutral
// - Fail-closed
//
// This contract does NOT:
// - generate receipts
// - mutate receipts
// - approve receipts
// - override receipts
// - compute pricing
// - create payment truth
//
// Receipt authority remains server-side.

class ReceiptContract {
  /// Canonical ride identity.
  final String rideId;

  /// Canonical receipt identity.
  final String receiptId;

  /// Receipt lifecycle status.
  final String status;

  /// Optional replay binding.
  final String? replayId;

  /// Optional receipt hash for traceability.
  final String? receiptHash;

  /// Optional issued-at timestamp from the server.
  final String? issuedAt;

  const ReceiptContract({
    required this.rideId,
    required this.receiptId,
    required this.status,
    this.replayId,
    this.receiptHash,
    this.issuedAt,
  });

  factory ReceiptContract.fromJson(
    Map<String, dynamic> json,
  ) {
    final rideId =
        (json["ride_id"] as String?)?.trim();

    final receiptId =
        (json["receipt_id"] as String?)?.trim();

    final status =
        (json["status"] as String?)?.trim();

    if (rideId == null || rideId.isEmpty) {
      throw ArgumentError(
        "missing_ride_id",
      );
    }

    if (receiptId == null ||
        receiptId.isEmpty) {
      throw ArgumentError(
        "missing_receipt_id",
      );
    }

    if (status == null || status.isEmpty) {
      throw ArgumentError(
        "missing_receipt_status",
      );
    }

    return ReceiptContract(
      rideId: rideId,
      receiptId: receiptId,
      status: status,
      replayId:
          (json["replay_id"] as String?)
              ?.trim(),
      receiptHash:
          (json["receipt_hash"] as String?)
              ?.trim(),
      issuedAt:
          (json["issued_at"] as String?)
              ?.trim(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      "ride_id": rideId,
      "receipt_id": receiptId,
      "status": status,
      "replay_id": replayId,
      "receipt_hash": receiptHash,
      "issued_at": issuedAt,
    };
  }

  bool get hasReplayBinding =>
      replayId != null &&
      replayId!.isNotEmpty;

  bool get hasReceiptHash =>
      receiptHash != null &&
      receiptHash!.isNotEmpty;

  bool get isCompleted =>
      status == "completed";

  bool get isEvidenceBound =>
      hasReplayBinding &&
      hasReceiptHash;

  @override
  String toString() {
    return "ReceiptContract("
        "rideId=$rideId, "
        "receiptId=$receiptId, "
        "status=$status"
        ")";
  }

  @override
  bool operator ==(Object other) {
    return other is ReceiptContract &&
        other.rideId == rideId &&
        other.receiptId == receiptId &&
        other.status == status;
  }

  @override
  int get hashCode =>
      Object.hash(
        rideId,
        receiptId,
        status,
      );
}