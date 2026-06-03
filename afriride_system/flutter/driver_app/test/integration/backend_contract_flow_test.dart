import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

import 'package:afriride_driver_pilot/api/afriride_api_client.dart';
import 'package:afriride_driver_pilot/contracts/earnings_contract.dart';
import 'package:afriride_driver_pilot/contracts/ledger_receipt_contract.dart';
import 'package:afriride_driver_pilot/contracts/receipt_contract.dart';
import 'package:afriride_driver_pilot/contracts/replay_contract.dart';
import 'package:afriride_driver_pilot/contracts/ride_contract.dart';
import 'package:afriride_driver_pilot/guards/driver_evidence_guard.dart';

class FakeBackendContractHttpClient extends http.BaseClient {
  int assignedRideCalls = 0;
  int acceptCalls = 0;
  int startCalls = 0;
  int completeCalls = 0;
  int receiptCalls = 0;
  int ledgerReceiptCalls = 0;
  int replayCalls = 0;
  int earningsCalls = 0;

  @override
  Future<http.StreamedResponse> send(
    http.BaseRequest request,
  ) async {
    final path = request.url.path;

    if (request.method == 'GET' &&
        path == '/driver/driver-1/rides/assigned') {
      assignedRideCalls++;

      return _jsonResponse({
        'rides': [
          {
            'ride_id': 'ride-1',
            'pickup': 'Pickup A',
            'dropoff': 'Dropoff B',
            'status': 'assigned',
            'assigned_driver_id': 'driver-1',
            'receipt_id': 'receipt-1',
            'replay_id': 'replay-1',
          },
        ],
      });
    }

    if (request.method == 'POST' &&
        path == '/ride/ride-1/accept') {
      acceptCalls++;
      return _jsonResponse({'ok': true});
    }

    if (request.method == 'POST' &&
        path == '/ride/ride-1/start') {
      startCalls++;
      return _jsonResponse({'ok': true});
    }

    if (request.method == 'POST' &&
        path == '/ride/ride-1/complete') {
      completeCalls++;
      return _jsonResponse({'ok': true});
    }

    if (request.method == 'GET' &&
        path == '/ride/ride-1/receipt') {
      receiptCalls++;

      return _jsonResponse({
        'ride_id': 'ride-1',
        'receipt_id': 'receipt-1',
        'status': 'completed',
        'replay_id': 'replay-1',
        'receipt_hash': 'receipt-hash-1',
        'issued_at': '2026-05-31T00:00:00Z',
      });
    }

    if (request.method == 'GET' &&
        path == '/ride/ride-1/ledger-receipt') {
      ledgerReceiptCalls++;

      return _jsonResponse({
        'receipt_id': 'ledger-receipt-ride-1',
        'verdict': 'VALID',
        'receipt_hash':
            'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
        'ledger_proof': {
          'event_count': 7,
          'root_hash':
              'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
          'hash_mode': 'sha256_canonical_chain',
        },
        'signature_validation': {
          'signature_mode': 'rsa_pss_sha256',
          'all_signatures_valid': true,
        },
        'identity_validation': {
          'all_verified': true,
        },
        'replay_proof': {
          'replay_valid': true,
        },
        'financial_summary': {
          'total_fare': 0,
        },
      });
    }

    if (request.method == 'GET' &&
        path == '/ride/ride-1/replay') {
      replayCalls++;

      return _jsonResponse({
        'ride_id': 'ride-1',
        'replay_id': 'replay-1',
        'replay_verified': true,
        'receipt_id': 'receipt-1',
        'replay_hash': 'replay-hash-1',
        'replay_epoch': 1,
      });
    }

    if (request.method == 'GET' &&
        path == '/driver/driver-1/earnings') {
      earningsCalls++;

      return _jsonResponse({
        'driver_id': 'driver-1',
        'daily_total': 125.50,
        'weekly_total': 650.75,
        'earnings_receipt_id': 'earnings-receipt-1',
        'earnings_period_id': 'week-2026-22',
        'replay_verified': true,
      });
    }

    return _jsonResponse(
      {'error': 'not_found'},
      statusCode: 404,
    );
  }

  http.StreamedResponse _jsonResponse(
    Map<String, dynamic> body, {
    int statusCode = 200,
  }) {
    return http.StreamedResponse(
      Stream<List<int>>.fromIterable(
        [
          utf8.encode(
            jsonEncode(body),
          ),
        ],
      ),
      statusCode,
      headers: {
        'content-type': 'application/json',
      },
    );
  }
}

void main() {
  test(
    'driver backend contract flow remains evidence-bound',
    () async {
      final fakeClient = FakeBackendContractHttpClient();

      final apiClient = AfriRideApiClient(
        baseUrl: 'https://example.invalid',
        client: fakeClient,
      );

      final rides =
          await apiClient.getAssignedRideRequests(
        driverId: 'driver-1',
      );

      expect(rides.length, 1);

      final RideContract ride = rides.first;

      DriverEvidenceGuard.validateDriverAssignment(
        ride,
        'driver-1',
      );

      await apiClient.acceptRide(
        rideId: ride.rideId,
        driverId: 'driver-1',
      );

      await apiClient.startRide(
        rideId: ride.rideId,
        driverId: 'driver-1',
      );

      await apiClient.completeRide(
        rideId: ride.rideId,
        driverId: 'driver-1',
      );

      final ReceiptContract receipt =
          await apiClient.getReceipt(
        rideId: ride.rideId,
      );

      DriverEvidenceGuard.validateReceipt(
        receipt,
      );

      DriverEvidenceGuard
          .validateCompletedReceipt(
        receipt,
      );

      final ReplayContract replay =
          await apiClient.getReplay(
        rideId: ride.rideId,
      );

      DriverEvidenceGuard.validateReplay(
        replay,
      );

      final LedgerReceiptContract ledgerReceipt =
          await apiClient.getLedgerReceipt(
        rideId: ride.rideId,
      );

      expect(
        ledgerReceipt.isValid &&
            ledgerReceipt.isCryptographic &&
            ledgerReceipt.isSigned,
        true,
      );

      final EarningsContract earnings =
          await apiClient.getEarnings(
        driverId: 'driver-1',
      );

 DriverEvidenceGuard.validateEarnings(
  earnings,
);

expect(
  earnings.driverId,
  'driver-1',
);

      expect(
        fakeClient.assignedRideCalls,
        1,
      );

      expect(
        fakeClient.acceptCalls,
        1,
      );

      expect(
        fakeClient.startCalls,
        1,
      );

      expect(
        fakeClient.completeCalls,
        1,
      );

      expect(
        fakeClient.receiptCalls,
        1,
      );

      expect(
        fakeClient.ledgerReceiptCalls,
        1,
      );

      expect(
        fakeClient.replayCalls,
        1,
      );

      expect(
        fakeClient.earningsCalls,
        1,
      );

      expect(
        receipt.receiptId,
        'receipt-1',
      );

      expect(
        replay.replayVerified,
        true,
      );

      expect(
        earnings.driverId,
        'driver-1',
      );
    },
  );
}
