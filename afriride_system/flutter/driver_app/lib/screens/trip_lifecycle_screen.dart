import 'package:flutter/material.dart';

import '../api/afriride_api_client.dart';
import '../contracts/ride_contract.dart';
import '../guards/driver_evidence_guard.dart';
import '../widgets/evidence_badge.dart';

/// Trip Lifecycle Screen
///
/// Purpose:
/// Displays a server-assigned ride and lets the driver request
/// server-authorized lifecycle transitions.
///
/// Constitutional Properties:
/// - API-bound
/// - evidence-guarded
/// - authority-neutral
/// - transition-request only
///
/// This screen does NOT:
/// - create trip authority
/// - compute pricing
/// - assign drivers
/// - mutate replay
/// - generate receipts
///
/// Driver requests transition.
/// Server authorizes transition.
class TripLifecycleScreen extends StatefulWidget {
  final String driverId;
  final RideContract ride;
  final AfriRideApiClient apiClient;

  const TripLifecycleScreen({
    super.key,
    required this.driverId,
    required this.ride,
    required this.apiClient,
  });

  @override
  State<TripLifecycleScreen> createState() =>
      _TripLifecycleScreenState();
}

class _TripLifecycleScreenState
    extends State<TripLifecycleScreen> {
  bool _loading = false;
  String? _error;

  Future<void> _runAction(
    Future<void> Function() action,
  ) async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      DriverEvidenceGuard.validateDriverAssignment(
        widget.ride,
        widget.driverId,
      );

      await action();

      if (!mounted) {
        return;
      }

      setState(() {
        _loading = false;
      });
    } catch (error) {
      if (!mounted) {
        return;
      }

      setState(() {
        _loading = false;
        _error = error.toString();
      });
    }
  }

  Future<void> _startRide() {
    return _runAction(
      () => widget.apiClient.startRide(
        rideId: widget.ride.rideId,
        driverId: widget.driverId,
      ),
    );
  }

  Future<void> _completeRide() {
    return _runAction(
      () => widget.apiClient.completeRide(
        rideId: widget.ride.rideId,
        driverId: widget.driverId,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    DriverEvidenceGuard.validateDriverAssignment(
      widget.ride,
      widget.driverId,
    );

    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text("Trip Lifecycle"),
      ),
      body: Padding(
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
                  "Assigned Trip",
                  style: theme.textTheme.titleLarge,
                ),
                const EvidenceBadge(
                  label: "Assignment",
                  verified: true,
                ),
              ],
            ),
            const SizedBox(height: 16),
            Text("Ride ID: ${widget.ride.rideId}"),
            const SizedBox(height: 8),
            Text("Pickup: ${widget.ride.pickup}"),
            const SizedBox(height: 8),
            Text("Dropoff: ${widget.ride.dropoff}"),
            const SizedBox(height: 8),
            Text("Status: ${widget.ride.status.name}"),
            const SizedBox(height: 24),
            if (_error != null) ...[
              Text(
                _error!,
                style: TextStyle(
                  color: theme.colorScheme.error,
                ),
              ),
              const SizedBox(height: 16),
            ],
            if (_loading)
              const Center(
                child: CircularProgressIndicator(),
              )
            else
              Row(
                children: [
                  ElevatedButton(
                    onPressed: _startRide,
                    child: const Text("Start Ride"),
                  ),
                  const SizedBox(width: 12),
                  OutlinedButton(
                    onPressed: _completeRide,
                    child: const Text("Complete Ride"),
                  ),
                ],
              ),
          ],
        ),
      ),
    );
  }
}