import '../contracts/earnings_contract.dart';
import '../contracts/receipt_contract.dart';
import '../contracts/replay_contract.dart';
import '../contracts/ride_contract.dart';

/// Driver evidence validation failure.
///
/// This exception is intentionally simple and deterministic.
/// It carries only a stable reason code.
///
/// The Driver App may display this reason.
/// The Driver App must not reinterpret it as authority.
class DriverEvidenceException implements Exception {
  final String reason;

  const DriverEvidenceException(this.reason);

  @override
  String toString() => reason;
}

/// Driver Evidence Guard
///
/// Purpose:
/// Validates evidence surfaces before the Driver App displays or acts on them.
///
/// Constitutional Properties:
/// - fail-closed
/// - deterministic
/// - read-only
/// - authority-neutral
///
/// This guard does NOT:
/// - compute pricing
/// - assign drivers
/// - rank drivers
/// - mutate replay
/// - generate receipts
/// - authorize payouts
///
/// It only rejects evidence that is incomplete,
/// mismatched, or outside the current tested boundary.
class DriverEvidenceGuard {
  const DriverEvidenceGuard._();

  static void validateRide(
    RideContract ride,
  ) {
    if (ride.rideId.trim().isEmpty) {
      throw const DriverEvidenceException(
        "missing_ride_id",
      );
    }

    if (ride.pickup.trim().isEmpty) {
      throw const DriverEvidenceException(
        "missing_pickup",
      );
    }

    if (ride.dropoff.trim().isEmpty) {
      throw const DriverEvidenceException(
        "missing_dropoff",
      );
    }

    if (ride.assignedDriverId.trim().isEmpty) {
      throw const DriverEvidenceException(
        "missing_assigned_driver_id",
      );
    }
  }

  static void validateReceipt(
    ReceiptContract receipt,
  ) {
    if (receipt.rideId.trim().isEmpty) {
      throw const DriverEvidenceException(
        "missing_receipt_ride_id",
      );
    }

    if (receipt.receiptId.trim().isEmpty) {
      throw const DriverEvidenceException(
        "missing_receipt_id",
      );
    }

    if (receipt.status.trim().isEmpty) {
      throw const DriverEvidenceException(
        "missing_receipt_status",
      );
    }
  }

  static void validateCompletedReceipt(
    ReceiptContract receipt,
  ) {
    validateReceipt(receipt);

    if (!receipt.isCompleted) {
      throw const DriverEvidenceException(
        "receipt_not_completed",
      );
    }
  }

  static void validateReplay(
    ReplayContract replay,
  ) {
    if (replay.rideId.trim().isEmpty) {
      throw const DriverEvidenceException(
        "missing_replay_ride_id",
      );
    }

    if (replay.replayId.trim().isEmpty) {
      throw const DriverEvidenceException(
        "missing_replay_id",
      );
    }

    if (!replay.replayVerified) {
      throw const DriverEvidenceException(
        "replay_not_verified",
      );
    }
  }

  static void validateDriverAssignment(
    RideContract ride,
    String driverId,
  ) {
    validateRide(ride);

    if (driverId.trim().isEmpty) {
      throw const DriverEvidenceException(
        "missing_driver_id",
      );
    }

    if (ride.assignedDriverId != driverId) {
      throw const DriverEvidenceException(
        "driver_assignment_mismatch",
      );
    }
  }

  static void validateEarnings(
    EarningsContract earnings,
  ) {
    if (earnings.driverId.trim().isEmpty) {
      throw const DriverEvidenceException(
        "missing_earnings_driver_id",
      );
    }

    if (earnings.dailyTotal < 0) {
      throw const DriverEvidenceException(
        "negative_daily_total",
      );
    }

    if (earnings.weeklyTotal < 0) {
      throw const DriverEvidenceException(
        "negative_weekly_total",
      );
    }
  }

  static void validateRideReceiptBinding(
    RideContract ride,
    ReceiptContract receipt,
  ) {
    validateRide(ride);
    validateReceipt(receipt);

    if (ride.rideId != receipt.rideId) {
      throw const DriverEvidenceException(
        "ride_receipt_mismatch",
      );
    }
  }

  static void validateRideReplayBinding(
    RideContract ride,
    ReplayContract replay,
  ) {
    validateRide(ride);
    validateReplay(replay);

    if (ride.rideId != replay.rideId) {
      throw const DriverEvidenceException(
        "ride_replay_mismatch",
      );
    }
  }

  static void validateReceiptReplayBinding(
    ReceiptContract receipt,
    ReplayContract replay,
  ) {
    validateReceipt(receipt);
    validateReplay(replay);

    if (receipt.rideId != replay.rideId) {
      throw const DriverEvidenceException(
        "receipt_replay_ride_mismatch",
      );
    }

    if (
        receipt.replayId != null &&
        receipt.replayId!.isNotEmpty &&
        receipt.replayId != replay.replayId) {
      throw const DriverEvidenceException(
        "receipt_replay_id_mismatch",
      );
    }
  }
}