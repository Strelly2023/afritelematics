import 'package:flutter/material.dart';

import '../contracts/ride_contract.dart';
import '../guards/driver_evidence_guard.dart';
import 'evidence_badge.dart';

/// Ride Card
///
/// Purpose:
/// Displays assigned ride evidence to the driver.
///
/// Constitutional Properties:
/// - display-only
/// - evidence-guarded
/// - authority-neutral
/// - API-action delegated
///
/// This widget does NOT:
/// - compute pricing
/// - assign drivers
/// - rank rides
/// - mutate replay
/// - generate receipts
///
/// Accept/reject actions must be handled through an API contract
/// by the parent screen.
class RideCard extends StatelessWidget {
  final RideContract ride;
  final String driverId;
  final VoidCallback? onAccept;
  final VoidCallback? onReject;

  const RideCard({
    super.key,
    required this.ride,
    required this.driverId,
    this.onAccept,
    this.onReject,
  });

  @override
  Widget build(BuildContext context) {
    DriverEvidenceGuard.validateDriverAssignment(
      ride,
      driverId,
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
                  "Assigned Ride",
                  style: theme.textTheme.titleMedium,
                ),
                const EvidenceBadge(
                  label: "Assignment",
                  verified: true,
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              "Ride ID: ${ride.rideId}",
              style: theme.textTheme.bodyMedium,
            ),
            const SizedBox(height: 8),
            Text(
              "Pickup: ${ride.pickup}",
              style: theme.textTheme.bodyMedium,
            ),
            const SizedBox(height: 8),
            Text(
              "Dropoff: ${ride.dropoff}",
              style: theme.textTheme.bodyMedium,
            ),
            const SizedBox(height: 8),
            Text(
              "Status: ${ride.status.name}",
              style: theme.textTheme.bodyMedium,
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                ElevatedButton(
                  onPressed: onAccept,
                  child: const Text("Accept"),
                ),
                const SizedBox(width: 12),
                OutlinedButton(
                  onPressed: onReject,
                  child: const Text("Reject"),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}