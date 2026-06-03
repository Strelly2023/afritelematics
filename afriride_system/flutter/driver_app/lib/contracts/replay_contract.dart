// Canonical Replay Evidence Contract
//
// Purpose:
// Represents replay evidence returned by the AfriRide API.
//
// Constitutional Properties:
// - Immutable
// - Read-only
// - Replay-safe
// - Evidence-only
// - Authority-neutral
//
// This contract does NOT:
// - generate replay
// - mutate replay
// - verify replay
// - authorize replay
// - override replay
//
// Replay truth remains server-side.
//
// The Driver App consumes replay evidence.
// The Driver App does not create replay authority.

class ReplayContract {
  /// Canonical ride identity.
  final String rideId;

  /// Canonical replay identity.
  final String replayId;

  /// Replay verification state.
  final bool replayVerified;

  /// Optional replay hash.
  final String? replayHash;

  /// Optional receipt binding.
  final String? receiptId;

  /// Optional replay epoch.
  final int? replayEpoch;

  const ReplayContract({
    required this.rideId,
    required this.replayId,
    required this.replayVerified,
    this.replayHash,
    this.receiptId,
    this.replayEpoch,
  });

  factory ReplayContract.fromJson(
    Map<String, dynamic> json,
  ) {
    final rideId =
        (json["ride_id"] as String?)?.trim();

    final replayId =
        (json["replay_id"] as String?)?.trim();

    final replayVerified =
        json["replay_verified"];

    if (rideId == null || rideId.isEmpty) {
      throw ArgumentError(
        "missing_ride_id",
      );
    }

    if (replayId == null ||
        replayId.isEmpty) {
      throw ArgumentError(
        "missing_replay_id",
      );
    }

    if (replayVerified is! bool) {
      throw ArgumentError(
        "invalid_replay_verified",
      );
    }

    final replayHash =
        (json["replay_hash"] as String?)
            ?.trim();

    final receiptId =
        (json["receipt_id"] as String?)
            ?.trim();

    final replayEpoch =
        json["replay_epoch"] as int?;

    if (replayEpoch != null &&
        replayEpoch < 0) {
      throw ArgumentError(
        "invalid_replay_epoch",
      );
    }

    return ReplayContract(
      rideId: rideId,
      replayId: replayId,
      replayVerified:
          replayVerified,
      replayHash: replayHash,
      receiptId: receiptId,
      replayEpoch: replayEpoch,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      "ride_id": rideId,
      "replay_id": replayId,
      "replay_verified":
          replayVerified,
      "replay_hash": replayHash,
      "receipt_id": receiptId,
      "replay_epoch": replayEpoch,
    };
  }

  bool get hasReplayHash =>
      replayHash != null &&
      replayHash!.isNotEmpty;

  bool get hasReceiptBinding =>
      receiptId != null &&
      receiptId!.isNotEmpty;

  bool get hasReplayEpoch =>
      replayEpoch != null;

  bool get isVerified =>
      replayVerified;

  bool get isEvidenceBound =>
      hasReplayHash &&
      hasReceiptBinding;

  @override
  String toString() {
    return
        "ReplayContract("
        "rideId=$rideId, "
        "replayId=$replayId, "
        "verified=$replayVerified"
        ")";
  }

  @override
  bool operator ==(
    Object other,
  ) {
    return other is ReplayContract &&
        other.rideId == rideId &&
        other.replayId == replayId &&
        other.replayVerified ==
            replayVerified;
  }

  @override
  int get hashCode =>
      Object.hash(
        rideId,
        replayId,
        replayVerified,
      );
}