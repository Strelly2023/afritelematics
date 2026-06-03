import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

import 'package:afriride_driver_pilot/api/afriride_api_client.dart';
import 'package:afriride_driver_pilot/contracts/ledger_receipt_contract.dart';
import 'package:afriride_driver_pilot/screens/ledger_receipt_screen.dart';

class FakeLedgerReceiptHttpClient extends http.BaseClient {
  int ledgerReceiptCalls = 0;

  @override
  Future<http.StreamedResponse> send(
    http.BaseRequest request,
  ) async {
    if (request.method == 'GET' &&
        request.url.path == '/ride/ride-1/ledger-receipt') {
      ledgerReceiptCalls += 1;
      return _jsonResponse(_ledgerReceiptJson());
    }

    return _jsonResponse({'error': 'not_found'}, statusCode: 404);
  }

  http.StreamedResponse _jsonResponse(
    Map<String, dynamic> body, {
    int statusCode = 200,
  }) {
    return http.StreamedResponse(
      Stream<List<int>>.fromIterable([utf8.encode(jsonEncode(body))]),
      statusCode,
      headers: {'content-type': 'application/json'},
    );
  }
}

void main() {
  test('ledger receipt contract parses portable proof summary', () {
    final receipt = LedgerReceiptContract.fromJson(_ledgerReceiptJson());

    expect(receipt.receiptId, 'ledger-receipt-ride-1');
    expect(receipt.isValid, true);
    expect(receipt.isCryptographic, true);
    expect(receipt.isSigned, true);
    expect(receipt.allSignaturesValid, true);
    expect(receipt.allIdentitiesVerified, true);
    expect(receipt.replayValid, true);
    expect(receipt.eventCount, 7);
    expect(receipt.totalFare, 0);
  });

  test('driver api fetches portable ledger receipt summary', () async {
    final fakeClient = FakeLedgerReceiptHttpClient();
    final apiClient = AfriRideApiClient(
      baseUrl: 'https://example.invalid',
      client: fakeClient,
    );

    final receipt = await apiClient.getLedgerReceipt(rideId: 'ride-1');

    expect(fakeClient.ledgerReceiptCalls, 1);
    expect(receipt.receiptHash.length, 64);
    expect(receipt.hashMode, 'sha256_canonical_chain');
  });

  testWidgets('ledger receipt screen displays portable proof summary', (tester) async {
    final fakeClient = FakeLedgerReceiptHttpClient();
    final apiClient = AfriRideApiClient(
      baseUrl: 'https://example.invalid',
      client: fakeClient,
    );

    await tester.pumpWidget(
      MaterialApp(
        home: LedgerReceiptScreen(
          rideId: 'ride-1',
          apiClient: apiClient,
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Portable Receipt'), findsOneWidget);
    expect(find.text('Receipt ID: ledger-receipt-ride-1'), findsOneWidget);
    expect(find.text('Verdict: VALID'), findsOneWidget);
    expect(find.text('Hash Mode: sha256_canonical_chain'), findsOneWidget);
    expect(find.text('Signature Mode: rsa_pss_sha256'), findsOneWidget);
    expect(find.text('Event Count: 7'), findsOneWidget);
    expect(find.text('Total Fare: 0.00'), findsOneWidget);
    expect(fakeClient.ledgerReceiptCalls, 1);
  });
}

Map<String, dynamic> _ledgerReceiptJson() {
  return {
    'receipt_id': 'ledger-receipt-ride-1',
    'generated_at': '2026-06-01T00:00:00Z',
    'ledger_proof': {
      'event_count': 7,
      'ride_count': 1,
      'completed_ride_count': 1,
      'root_hash':
          'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
      'hash_mode': 'sha256_canonical_chain',
      'chain_valid': true,
    },
    'signature_validation': {
      'signature_mode': 'rsa_pss_sha256',
      'all_signatures_valid': true,
      'invalid_signatures': [],
    },
    'identity_validation': {
      'all_verified': true,
      'unverified_identities': [],
    },
    'replay_proof': {
      'replay_valid': true,
      'replay_hash_match': true,
    },
    'financial_summary': {
      'total_fare': 0,
    },
    'verdict': 'VALID',
    'receipt_hash':
        'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
  };
}
