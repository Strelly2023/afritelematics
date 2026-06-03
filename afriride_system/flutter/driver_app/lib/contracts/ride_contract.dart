// Canonical Driver Ride Contract
//
// Purpose:
// Represents an assigned ride returned by an AfriRide API.
//
// Constitutional Properties:
// - Read-only
// - Immutable
// - Authority-neutral
// - Replay-safe
// - Evidence-compatible
//
// This contract does NOT:
// - compute pricing
// - assign drivers
// - rank drivers
// - mutate replay
// - generate receipts
//
// It is an evidence carrier only.

enum RideStatus {
  assigned,
  accepted,
  arrived,
  inProgress,
  completed,
  cancelled,
}

class RideContract {
  final String rideId;
  final String pickup;
  final String dropoff;
  final RideStatus status;
  final String assignedDriverId;

  /// Optional evidence references.
  final String? receiptId;
  final String? replayId;

  const RideContract({
    required this.rideId,
    required this.pickup,
    required this.dropoff,
    required this.status,
    required this.assignedDriverId,
    this.receiptId,
    this.replayId,
  });

  factory RideContract.fromJson(
    Map<String, dynamic> json,
  ) {
    final rideId =
        (json["ride_id"] as String?)?.trim();

    final pickup =
        (json["pickup"] as String?)?.trim();

    final dropoff =
        (json["dropoff"] as String?)?.trim();

    final assignedDriverId =
        (json["assigned_driver_id"] as String?)
            ?.trim();

    final statusValue =
        (json["status"] as String?)?.trim();

    if (rideId == null || rideId.isEmpty) {
      throw ArgumentError(
        "missing_ride_id",
      );
    }

    if (pickup == null || pickup.isEmpty) {
      throw ArgumentError(
        "missing_pickup",
      );
    }

    if (dropoff == null || dropoff.isEmpty) {
      throw ArgumentError(
        "missing_dropoff",
      );
    }

    if (assignedDriverId == null ||
        assignedDriverId.isEmpty) {
      throw ArgumentError(
        "missing_assigned_driver_id",
      );
    }

    if (statusValue == null ||
        statusValue.isEmpty) {
      throw ArgumentError(
        "missing_status",
      );
    }

    return RideContract(
      rideId: rideId,
      pickup: pickup,
      dropoff: dropoff,
      assignedDriverId: assignedDriverId,
      status: _parseStatus(statusValue),
      receiptId:
          (json["receipt_id"] as String?)
              ?.trim(),
      replayId:
          (json["replay_id"] as String?)
              ?.trim(),
    );
  }

  static RideStatus _parseStatus(
    String value,
  ) {
    switch (value) {
      case "assigned":
        return RideStatus.assigned;
      case "accepted":
        return RideStatus.accepted;
      case "arrived":
        return RideStatus.arrived;
      case "in_progress":
        return RideStatus.inProgress;
      case "completed":
        return RideStatus.completed;
      case "cancelled":
        return RideStatus.cancelled;
      default:
        throw ArgumentError(
          "invalid_ride_status: $value",
        );
    }
  }

  static String _statusToJson(
    RideStatus status,
  ) {
    switch (status) {
      case RideStatus.assigned:
        return "assigned";
      case RideStatus.accepted:
        return "accepted";
      case RideStatus.arrived:
        return "arrived";
      case RideStatus.inProgress:
        return "in_progress";
      case RideStatus.completed:
        return "completed";
      case RideStatus.cancelled:
        return "cancelled";
    }
  }

  Map<String, dynamic> toJson() {
    return {
      "ride_id": rideId,
      "pickup": pickup,
      "dropoff": dropoff,
      "status": _statusToJson(status),
      "assigned_driver_id": assignedDriverId,
      "receipt_id": receiptId,
      "replay_id": replayId,
    };
  }

  bool get hasReceipt =>
      receiptId != null &&
      receiptId!.isNotEmpty;

  bool get hasReplay =>
      replayId != null &&
      replayId!.isNotEmpty;

  bool get isEvidenceBound =>
      hasReceipt &&
      hasReplay;

  RideContract copyWith({
    String? receiptId,
    String? replayId,
  }) {
    return RideContract(
      rideId: rideId,
      pickup: pickup,
      dropoff: dropoff,
      status: status,
      assignedDriverId: assignedDriverId,
      receiptId: receiptId ?? this.receiptId,
      replayId: replayId ?? this.replayId,
    );
  }

  @override
  String toString() {
    return
        "RideContract("
        "rideId=$rideId, "
        "status=${_statusToJson(status)}, "
        "assignedDriverId=$assignedDriverId"
        ")";
  }

  @override
  bool operator ==(
    Object other,
  ) {
    return other is RideContract &&
        other.rideId == rideId &&
        other.assignedDriverId ==
            assignedDriverId &&
        other.status == status;
  }

  @override
  int get hashCode =>
      Object.hash(
        rideId,
        assignedDriverId,
        status,
      );
}