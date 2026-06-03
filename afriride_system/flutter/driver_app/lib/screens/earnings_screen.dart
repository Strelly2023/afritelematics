import 'package:flutter/material.dart';

import '../api/afriride_api_client.dart';
import '../contracts/earnings_contract.dart';
import '../guards/driver_evidence_guard.dart';
import '../widgets/earnings_tile.dart';

/// Earnings Screen
///
/// Purpose:
/// Displays server-issued driver earnings evidence.
///
/// Constitutional Properties:
/// - API-bound
/// - evidence-guarded
/// - display-only
/// - authority-neutral
///
/// This screen does NOT:
/// - calculate earnings
/// - compute pricing
/// - authorize payouts
/// - settle balances
/// - generate earnings evidence
///
/// Driver App displays earnings evidence.
/// Server remains earnings authority.
class EarningsScreen extends StatefulWidget {
  final String driverId;
  final AfriRideApiClient apiClient;

  const EarningsScreen({
    super.key,
    required this.driverId,
    required this.apiClient,
  });

  @override
  State<EarningsScreen> createState() =>
      _EarningsScreenState();
}

class _EarningsScreenState extends State<EarningsScreen> {
  late Future<EarningsContract> _earningsFuture;

  @override
  void initState() {
    super.initState();
    _earningsFuture = _loadEarnings();
  }

  Future<EarningsContract> _loadEarnings() async {
    final earnings = await widget.apiClient.getEarnings(
      driverId: widget.driverId,
    );

    DriverEvidenceGuard.validateEarnings(
      earnings,
    );

    if (earnings.driverId != widget.driverId) {
      throw const DriverEvidenceException(
        "earnings_driver_mismatch",
      );
    }

    return earnings;
  }

  Future<void> _refresh() async {
    setState(() {
      _earningsFuture = _loadEarnings();
    });

    await _earningsFuture;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Earnings"),
      ),
      body: FutureBuilder<EarningsContract>(
        future: _earningsFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState ==
              ConnectionState.waiting) {
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

          final earnings = snapshot.data;

          if (earnings == null) {
            return const _EmptyState();
          }

          return RefreshIndicator(
            onRefresh: _refresh,
            child: ListView(
              children: [
                EarningsTile(
                  earnings: earnings,
                ),
              ],
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
      child: Text("No earnings evidence available"),
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
              "Unable to load earnings evidence",
              style:
                  Theme.of(context).textTheme.titleMedium,
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