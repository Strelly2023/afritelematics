import 'package:flutter/material.dart';

import '../api/afriride_api_client.dart';
import '../contracts/ride_contract.dart';
import '../guards/driver_evidence_guard.dart';
import '../widgets/ride_card.dart';

/// Ride Requests Screen
///
/// Purpose:
/// Displays server-assigned ride requests for a driver.
///
/// Constitutional Properties:
/// - API-bound
/// - evidence-guarded
/// - authority-neutral
/// - display/action delegation only
///
/// This screen does NOT:
/// - compute pricing
/// - assign drivers
/// - rank rides
/// - mutate replay
/// - generate receipts
///
/// Driver accepts/rejects through API contract only.
/// Server remains the authority.
class RideRequestsScreen extends StatefulWidget {
  final String driverId;
  final AfriRideApiClient apiClient;
  final ValueChanged<RideContract>? onRideSelected;

  const RideRequestsScreen({
    super.key,
    required this.driverId,
    required this.apiClient,
    this.onRideSelected,
  });

  @override
  State<RideRequestsScreen> createState() => _RideRequestsScreenState();
}

class _RideRequestsScreenState extends State<RideRequestsScreen> {
  late Future<List<RideContract>> _ridesFuture;

  @override
  void initState() {
    super.initState();
    _ridesFuture = _loadAssignedRides();
  }

  Future<List<RideContract>> _loadAssignedRides() async {
    final rides = await widget.apiClient.getAssignedRideRequests(
      driverId: widget.driverId,
    );

    for (final ride in rides) {
      DriverEvidenceGuard.validateDriverAssignment(
        ride,
        widget.driverId,
      );
    }

    return rides;
  }

  Future<void> _refresh() async {
    setState(() {
      _ridesFuture = _loadAssignedRides();
    });

    await _ridesFuture;
  }

  Future<void> _acceptRide(
    RideContract ride,
  ) async {
    DriverEvidenceGuard.validateDriverAssignment(
      ride,
      widget.driverId,
    );

    await widget.apiClient.acceptRide(
      rideId: ride.rideId,
      driverId: widget.driverId,
    );

    widget.onRideSelected?.call(ride);

    await _refresh();
  }

  Future<void> _rejectRide(
    RideContract ride,
  ) async {
    DriverEvidenceGuard.validateDriverAssignment(
      ride,
      widget.driverId,
    );

    await widget.apiClient.rejectRide(
      rideId: ride.rideId,
      driverId: widget.driverId,
    );

    await _refresh();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Ride Requests"),
      ),
      body: FutureBuilder<List<RideContract>>(
        future: _ridesFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(
              child: CircularProgressIndicator(),
            );
          }

          if (snapshot.hasError) {
            return _ErrorState(
              message: snapshot.error.toString(),
              onRetry: _refresh,
            );
          }

          final rides = snapshot.data ?? [];

          if (rides.isEmpty) {
            return const _EmptyState();
          }

          return RefreshIndicator(
            onRefresh: _refresh,
            child: ListView.builder(
              itemCount: rides.length,
              itemBuilder: (context, index) {
                final ride = rides[index];

                return RideCard(
                  ride: ride,
                  driverId: widget.driverId,
                  onAccept: () => _acceptRide(ride),
                  onReject: () => _rejectRide(ride),
                );
              },
            ),
          );
        },
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState();

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Text("No assigned ride requests"),
    );
  }
}

class _ErrorState extends StatelessWidget {
  final String message;
  final Future<void> Function() onRetry;

  const _ErrorState({
    required this.message,
    required this.onRetry,
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              "Unable to load ride requests",
              style: Theme.of(context).textTheme.titleMedium,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              message,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: onRetry,
              child: const Text("Retry"),
            ),
          ],
        ),
      ),
    );
  }
}
