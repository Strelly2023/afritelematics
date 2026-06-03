import 'package:flutter/material.dart';

import '../api/afriride_api_client.dart';
import '../contracts/ledger_receipt_contract.dart';
import '../widgets/evidence_badge.dart';

/// Ledger Receipt Screen
///
/// Displays server-derived portable proof receipts.
///
/// This screen does not verify, generate, or mutate proof. It only displays
/// server-issued evidence summaries.
class LedgerReceiptScreen extends StatefulWidget {
  final String rideId;
  final AfriRideApiClient apiClient;

  const LedgerReceiptScreen({
    super.key,
    required this.rideId,
    required this.apiClient,
  });

  @override
  State<LedgerReceiptScreen> createState() => _LedgerReceiptScreenState();
}

class _LedgerReceiptScreenState extends State<LedgerReceiptScreen> {
  late Future<LedgerReceiptContract> _receiptFuture;

  @override
  void initState() {
    super.initState();
    _receiptFuture = widget.apiClient.getLedgerReceipt(
      rideId: widget.rideId,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Ledger Receipt'),
      ),
      body: FutureBuilder<LedgerReceiptContract>(
        future: _receiptFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }

          if (snapshot.hasError) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Text(
                  'Unable to load ledger receipt\n${snapshot.error}',
                  textAlign: TextAlign.center,
                ),
              ),
            );
          }

          final receipt = snapshot.data;
          if (receipt == null) {
            return const Center(child: Text('No ledger receipt available'));
          }

          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              _LedgerReceiptPanel(receipt: receipt),
            ],
          );
        },
      ),
    );
  }
}

class _LedgerReceiptPanel extends StatelessWidget {
  final LedgerReceiptContract receipt;

  const _LedgerReceiptPanel({
    required this.receipt,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Portable Receipt',
                  style: theme.textTheme.titleMedium,
                ),
                EvidenceBadge(
                  label: 'Receipt',
                  verified: receipt.isValid &&
                      receipt.isCryptographic &&
                      receipt.isSigned &&
                      receipt.allSignaturesValid &&
                      receipt.allIdentitiesVerified &&
                      receipt.replayValid,
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text('Receipt ID: ${receipt.receiptId}'),
            const SizedBox(height: 8),
            Text('Verdict: ${receipt.verdict}'),
            const SizedBox(height: 8),
            Text('Hash Mode: ${receipt.hashMode}'),
            const SizedBox(height: 8),
            Text('Signature Mode: ${receipt.signatureMode}'),
            const SizedBox(height: 8),
            Text('Event Count: ${receipt.eventCount}'),
            const SizedBox(height: 8),
            Text('Total Fare: ${receipt.totalFare.toStringAsFixed(2)}'),
            const SizedBox(height: 8),
            Text('Root Hash: ${receipt.rootHash}'),
            const SizedBox(height: 8),
            Text('Receipt Hash: ${receipt.receiptHash}'),
          ],
        ),
      ),
    );
  }
}
