import 'package:flutter/material.dart';

import '../api/afriride_api_client.dart';
import '../contracts/replay_contract.dart';
import '../guards/driver_evidence_guard.dart';
import '../widgets/evidence_badge.dart';

/// Replay Screen
///
/// Purpose:
/// Displays server-issued replay evidence for a completed ride.
///
/// Constitutional Properties:
/// - API-bound
/// - evidence-guarded
/// - display-only
/// - read-only
/// - authority-neutral
///
/// This screen does NOT:
/// - verify replay locally
/// - approve replay
/// - override replay
/// - mutate replay
/// - generate replay
/// - generate receipts
///
/// Replay authority remains server-side.
class ReplayScreen extends StatefulWidget {
  final String rideId;
  final AfriRideApiClient apiClient;

  const ReplayScreen({
    super.key,
    required this.rideId,
    required this.apiClient,
  });

  @override
  State<ReplayScreen> createState() => _ReplayScreenState();
}

class _ReplayScreenState extends State<ReplayScreen> {
  late Future<ReplayContract> _replayFuture;

  @override
  void initState() {
    super.initState();
    _replayFuture = _loadReplay();
  }

  Future<ReplayContract> _loadReplay() async {
    final replay = await widget.apiClient.getReplay(
      rideId: widget.rideId,
    );

    DriverEvidenceGuard.validateReplay(
      replay,
    );

    if (replay.rideId != widget.rideId) {
      throw const DriverEvidenceException(
        "replay_ride_mismatch",
      );
    }

    return replay;
  }

  Future<void> _refresh() async {
    setState(() {
      _replayFuture = _loadReplay();
    });

    await _replayFuture;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Replay Evidence"),
      ),
      body: FutureBuilder<ReplayContract>(
        future: _replayFuture,
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

          final replay = snapshot.data;

          if (replay == null) {
            return const _EmptyState();
          }

          return RefreshIndicator(
            onRefresh: _refresh,
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                _ReplayEvidencePanel(
                  replay: replay,
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}

class _ReplayEvidencePanel extends StatelessWidget {
  final ReplayContract replay;

  const _ReplayEvidencePanel({
    required this.replay,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Card(
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
                  "Replay Evidence",
                  style: theme.textTheme.titleMedium,
                ),
                EvidenceBadge(
                  label: "Replay",
                  verified: replay.replayVerified,
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              "Ride ID: ${replay.rideId}",
              style: theme.textTheme.bodyMedium,
            ),
            const SizedBox(height: 8),
            Text(
              "Replay ID: ${replay.replayId}",
              style: theme.textTheme.bodyMedium,
            ),
            if (replay.hasReplayHash) ...[
              const SizedBox(height: 8),
              Text(
                "Replay Hash: ${replay.replayHash}",
                style: theme.textTheme.bodyMedium,
              ),
            ],
            if (replay.hasReceiptBinding) ...[
              const SizedBox(height: 8),
              Text(
                "Receipt Binding: ${replay.receiptId}",
                style: theme.textTheme.bodyMedium,
              ),
            ],
            if (replay.replayEpoch != null) ...[
              const SizedBox(height: 8),
              Text(
                "Replay Epoch: ${replay.replayEpoch}",
                style: theme.textTheme.bodyMedium,
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState();

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Text("No replay evidence available"),
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
              "Unable to load replay evidence",
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