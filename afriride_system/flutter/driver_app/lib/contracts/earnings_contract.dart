// Canonical Earnings Evidence Contract
//
// Purpose:
// Represents driver earnings evidence returned by the AfriRide API.
//
// Constitutional Properties:
// - Immutable
// - Read-only
// - Evidence-only
// - Authority-neutral
// - Fail-closed
//
// This contract does NOT:
// - calculate earnings
// - generate earnings
// - authorize payouts
// - modify balances
// - compute ride pricing
//
// Earnings authority remains server-side.

class EarningsContract {
  /// Driver identifier.
  final String driverId;

  /// Daily earnings total.
  final double dailyTotal;

  /// Weekly earnings total.
  final double weeklyTotal;

  /// Optional payout period identifier.
  final String? earningsPeriodId;

  /// Optional earnings receipt identifier.
  final String? earningsReceiptId;

  /// Optional replay verification state.
  final bool? replayVerified;

  /// Optional earnings evidence timestamp.
  final String? generatedAt;

  const EarningsContract({
    required this.driverId,
    required this.dailyTotal,
    required this.weeklyTotal,
    this.earningsPeriodId,
    this.earningsReceiptId,
    this.replayVerified,
    this.generatedAt,
  });

  factory EarningsContract.fromJson(
    Map<String, dynamic> json,
  ) {
    final driverId =
        (json["driver_id"] as String?)?.trim();

    if (driverId == null || driverId.isEmpty) {
      throw ArgumentError(
        "missing_driver_id",
      );
    }

    final daily = json["daily_total"];
    final weekly = json["weekly_total"];

    if (daily is! num) {
      throw ArgumentError(
        "invalid_daily_total",
      );
    }

    if (weekly is! num) {
      throw ArgumentError(
        "invalid_weekly_total",
      );
    }

    if (daily < 0) {
      throw ArgumentError(
        "negative_daily_total",
      );
    }

    if (weekly < 0) {
      throw ArgumentError(
        "negative_weekly_total",
      );
    }

    return EarningsContract(
      driverId: driverId,
      dailyTotal: daily.toDouble(),
      weeklyTotal: weekly.toDouble(),
      earningsPeriodId:
          (json["earnings_period_id"] as String?)
              ?.trim(),
      earningsReceiptId:
          (json["earnings_receipt_id"] as String?)
              ?.trim(),
      replayVerified:
          json["replay_verified"] as bool?,
      generatedAt:
          (json["generated_at"] as String?)
              ?.trim(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      "driver_id": driverId,
      "daily_total": dailyTotal,
      "weekly_total": weeklyTotal,
      "earnings_period_id": earningsPeriodId,
      "earnings_receipt_id": earningsReceiptId,
      "replay_verified": replayVerified,
      "generated_at": generatedAt,
    };
  }

  bool get hasReceiptEvidence =>
      earningsReceiptId != null &&
      earningsReceiptId!.isNotEmpty;

  bool get hasPeriodEvidence =>
      earningsPeriodId != null &&
      earningsPeriodId!.isNotEmpty;

  bool get isReplayVerified =>
      replayVerified == true;

  @override
  String toString() {
    return
        "EarningsContract("
        "driverId=$driverId, "
        "dailyTotal=$dailyTotal, "
        "weeklyTotal=$weeklyTotal"
        ")";
  }

  @override
  bool operator ==(Object other) {
    return other is EarningsContract &&
        other.driverId == driverId &&
        other.dailyTotal == dailyTotal &&
        other.weeklyTotal == weeklyTotal;
  }

  @override
  int get hashCode =>
      Object.hash(
        driverId,
        dailyTotal,
        weeklyTotal,
      );
}