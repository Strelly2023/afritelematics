import 'package:flutter/material.dart';

import '../contracts/earnings_contract.dart';
import '../guards/driver_evidence_guard.dart';
import 'evidence_badge.dart';

/// Earnings Tile
///
/// Purpose:
/// Displays server-issued driver earnings evidence.
///
/// Constitutional Properties:
/// - display-only
/// - evidence-guarded
/// - authority-neutral
/// - read-only
///
/// This widget does NOT:
/// - calculate earnings
/// - compute ride pricing
/// - authorize payouts
/// - settle balances
/// - mutate earnings evidence
///
/// Earnings authority remains server-side.
class EarningsTile extends StatelessWidget {
  final EarningsContract earnings;

  const EarningsTile({
    super.key,
    required this.earnings,
  });

  @override
  Widget build(BuildContext context) {
    DriverEvidenceGuard.validateEarnings(
      earnings,
    );

    final theme = Theme.of(context);

    return Card(
      margin: const EdgeInsets.all(12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment:
              CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment:
                  MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  "Earnings Evidence",
                  style: theme.textTheme.titleMedium,
                ),
                EvidenceBadge(
                  label: "Replay",
                  verified:
                      earnings.isReplayVerified,
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              "Driver ID: ${earnings.driverId}",
              style: theme.textTheme.bodyMedium,
            ),
            const SizedBox(height: 8),
            Text(
              "Daily Total: ${earnings.dailyTotal.toStringAsFixed(2)}",
              style: theme.textTheme.bodyMedium,
            ),
            const SizedBox(height: 8),
            Text(
              "Weekly Total: ${earnings.weeklyTotal.toStringAsFixed(2)}",
              style: theme.textTheme.bodyMedium,
            ),
            if (earnings.hasReceiptEvidence) ...[
              const SizedBox(height: 8),
              Text(
                "Receipt Evidence: ${earnings.earningsReceiptId}",
                style: theme.textTheme.bodyMedium,
              ),
            ],
            if (earnings.hasPeriodEvidence) ...[
              const SizedBox(height: 8),
              Text(
                "Period Evidence: ${earnings.earningsPeriodId}",
                style: theme.textTheme.bodyMedium,
              ),
            ],
          ],
        ),
      ),
    );
  }
}