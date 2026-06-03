import 'package:flutter/material.dart';

import 'api/afriride_api_client.dart';
import 'contracts/ride_contract.dart';
import 'screens/earnings_screen.dart';
import 'screens/replay_screen.dart';
import 'screens/ride_requests_screen.dart';
import 'screens/trip_lifecycle_screen.dart';

/// AfriRide Driver App
///
/// Purpose:
/// Provides the runnable Driver App shell for verified driver workflows.
///
/// Constitutional Properties:
/// - UI-only
/// - API-bound
/// - evidence-consuming
/// - authority-neutral
/// - replay-read-only
/// - receipt-read-only
/// - earnings-read-only
///
/// This app shell does NOT:
/// - compute pricing
/// - assign drivers
/// - rank rides
/// - mutate replay
/// - approve replay
/// - generate receipts
/// - authorize payouts
/// - create dispatch authority
///
/// Driver actions are delegated through AfriRideApiClient.
/// Server-side systems remain the authority.
void main() {
  runApp(
    AfriRideDriverApp(
      driverId: const String.fromEnvironment(
        'AFRIRIDE_DRIVER_ID',
        defaultValue: 'driver-1',
      ),
      apiClient: AfriRideApiClient(
        baseUrl: const String.fromEnvironment(
          'AFRIRIDE_API_BASE_URL',
          defaultValue: 'https://example.invalid',
        ),
      ),
    ),
  );
}

class AfriRideDriverApp extends StatelessWidget {
  final String driverId;
  final AfriRideApiClient apiClient;

  const AfriRideDriverApp({
    super.key,
    required this.driverId,
    required this.apiClient,
  });

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'AfriRide Driver',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.teal,
        ),
        useMaterial3: true,
      ),
      home: DriverHomeShell(
        driverId: driverId,
        apiClient: apiClient,
      ),
    );
  }
}

class DriverHomeShell extends StatefulWidget {
  final String driverId;
  final AfriRideApiClient apiClient;

  const DriverHomeShell({
    super.key,
    required this.driverId,
    required this.apiClient,
  });

  @override
  State<DriverHomeShell> createState() => _DriverHomeShellState();
}

class _DriverHomeShellState extends State<DriverHomeShell> {
  int _selectedIndex = 0;

  /// Temporary contract-bound ride reference for screen integration.
  ///
  /// This is not dispatch authority.
  /// It does not assign a driver.
  /// It does not calculate pricing.
  /// It only supplies the already-assigned ride identity needed by
  /// currently verified screens until navigation is wired to selected
  /// ride state from RideRequestsScreen.
  RideContract get _selectedRide {
    return RideContract(
      rideId: 'ride-1',
      pickup: 'Pickup A',
      dropoff: 'Dropoff B',
      status: RideStatus.accepted,
      assignedDriverId: widget.driverId,
      receiptId: 'receipt-1',
      replayId: 'replay-1',
    );
  }

  void _selectTab(int index) {
    setState(() {
      _selectedIndex = index;
    });
  }

  @override
  Widget build(BuildContext context) {
    final pages = <Widget>[
      RideRequestsScreen(
        driverId: widget.driverId,
        apiClient: widget.apiClient,
      ),
      TripLifecycleScreen(
        driverId: widget.driverId,
        ride: _selectedRide,
        apiClient: widget.apiClient,
      ),
      ReplayScreen(
        rideId: _selectedRide.rideId,
        apiClient: widget.apiClient,
      ),
      EarningsScreen(
        driverId: widget.driverId,
        apiClient: widget.apiClient,
      ),
    ];

    return Scaffold(
      body: IndexedStack(
        index: _selectedIndex,
        children: pages,
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _selectedIndex,
        onDestinationSelected: _selectTab,
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.local_taxi_outlined),
            selectedIcon: Icon(Icons.local_taxi),
            label: 'Requests',
          ),
          NavigationDestination(
            icon: Icon(Icons.route_outlined),
            selectedIcon: Icon(Icons.route),
            label: 'Trip',
          ),
          NavigationDestination(
            icon: Icon(Icons.verified_outlined),
            selectedIcon: Icon(Icons.verified),
            label: 'Replay',
          ),
          NavigationDestination(
            icon: Icon(Icons.payments_outlined),
            selectedIcon: Icon(Icons.payments),
            label: 'Earnings',
          ),
        ],
      ),
    );
  }
}