import 'package:flutter/material.dart';

import '../verifier/portable_receipt_verifier.dart';

class VerifierScreen extends StatefulWidget {
  const VerifierScreen({super.key});

  @override
  State<VerifierScreen> createState() => _VerifierScreenState();
}

class _VerifierScreenState extends State<VerifierScreen> {
  final TextEditingController _controller = TextEditingController();
  PortableVerificationResult? _result;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _loadDemo() {
    setState(() {
      _controller.text = buildDemoPrivacyQrPayload();
      _result = null;
    });
  }

  void _verify() {
    setState(() {
      _result = verifyPrivacyQrPayload(_controller.text);
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Verifier'),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Scan or paste a privacy QR payload',
                        style: theme.textTheme.titleMedium,
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'This screen verifies the QR envelope, zk receipt, and cross-chain bridge statelessly.',
                        style: theme.textTheme.bodyMedium,
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _controller,
                maxLines: 8,
                minLines: 6,
                decoration: const InputDecoration(
                  labelText: 'QR payload',
                  alignLabelWithHint: true,
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 12),
              Wrap(
                spacing: 12,
                runSpacing: 12,
                children: [
                  FilledButton.tonal(
                    onPressed: _loadDemo,
                    child: const Text('Load demo'),
                  ),
                  FilledButton(
                    onPressed: _verify,
                    child: const Text('Verify'),
                  ),
                ],
              ),
              if (_result != null) ...[
                const SizedBox(height: 20),
                _VerificationCard(result: _result!),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class _VerificationCard extends StatelessWidget {
  final PortableVerificationResult result;

  const _VerificationCard({
    required this.result,
  });

  Color _toneColor(BuildContext context) {
    if (result.valid) {
      return Colors.green;
    }
    if (result.trustLevel == 'PARTIAL') {
      return Colors.orange;
    }
    return Theme.of(context).colorScheme.error;
  }

  IconData _icon() {
    if (result.valid) {
      return Icons.verified;
    }
    if (result.trustLevel == 'PARTIAL') {
      return Icons.privacy_tip_outlined;
    }
    return Icons.error_outline;
  }

  @override
  Widget build(BuildContext context) {
    final payload = result.payload ?? {};
    final zkReceipt = result.zkReceipt ?? {};
    final bridge = result.bridge ?? {};

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(_icon(), color: _toneColor(context)),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    result.valid ? 'VERIFIED' : 'INVALID',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          color: _toneColor(context),
                          fontWeight: FontWeight.w700,
                        ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text('Reason: ${result.reason}'),
            const SizedBox(height: 8),
            Text('Trust Level: ${result.trustLevel}'),
            if (zkReceipt.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text('ZK Commitment: ${zkReceipt['commitment'] ?? 'n/a'}'),
              Text(
                'Receipt Hash: ${(zkReceipt['public_inputs'] is Map) ? zkReceipt['public_inputs']['receipt_hash'] : 'n/a'}',
              ),
            ],
            if (bridge.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text('Bridge Hash: ${bridge['bridge_hash'] ?? 'n/a'}'),
              Text(
                'Chain: ${(bridge['light_client_state'] is Map) ? bridge['light_client_state']['chain_id'] : 'n/a'}',
              ),
            ],
            if (payload.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text('QR Type: ${payload['type'] ?? 'n/a'}'),
              Text('Issued At: ${payload['issued_at'] ?? 'n/a'}'),
            ],
          ],
        ),
      ),
    );
  }
}
