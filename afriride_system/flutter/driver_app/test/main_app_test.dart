import 'dart:convert';

//import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

import 'package:afriride_driver_pilot/api/afriride_api_client.dart';
import 'package:afriride_driver_pilot/main.dart';

class FakeMainAppHttpClient extends http.BaseClient {
  int assignedRideCalls = 0;
  int replayCalls = 0;
  int earningsCalls = 0;
  int startCalls = 0;
  int completeCalls = 0;

  @override
  Future<http.StreamedResponse> send(
    http.BaseRequest request,
  ) async {
    final path = request.url.path;

    if (request.method == 'GET' &&
        path == '/driver/driver-1/rides/assigned') {
      assignedRideCalls += 1;

      return _jsonResponse({
        'rides': [
          {
            'ride_id': 'ride-1',
            'pickup': 'Pickup A',
            'dropoff': 'Dropoff B',
            'status': 'assigned',
            'assigned_driver_id': 'driver-1',
          },
        ],
      });
    }

    if (request.method == 'POST' &&
        path == '/ride/ride-1/start') {
      startCalls += 1;
      return _jsonResponse({'ok': true});
    }

    if (request.method == 'POST' &&
        path == '/ride/ride-1/complete') {
      completeCalls += 1;
      return _jsonResponse({'ok': true});
    }

    if (request.method == 'GET' &&
        path == '/ride/ride-1/replay') {
      replayCalls += 1;

      return _jsonResponse({
        'ride_id': 'ride-1',
        'replay_id': 'replay-1',
        'replay_verified': true,
        'replay_hash': 'hash-1',
        'receipt_id': 'receipt-1',
        'replay_epoch': 1,
      });
    }

    if (request.method == 'GET' &&
        path == '/driver/driver-1/earnings') {
      earningsCalls += 1;

      return _jsonResponse({
        'driver_id': 'driver-1',
        'daily_total': 50,
        'weekly_total': 300,
        'earnings_receipt_id': 'earnings-receipt-1',
        'earnings_period_id': 'period-1',
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
  testWidgets(
    'driver app shell renders verified navigation surfaces',
    (tester) async {
      final fakeClient = FakeMainAppHttpClient();

      final apiClient = AfriRideApiClient(
        baseUrl: 'https://example.invalid',
        client: fakeClient,
      );

      await tester.pumpWidget(
        AfriRideDriverApp(
          driverId: 'driver-1',
          apiClient: apiClient,
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text('Ride Requests'), findsOneWidget);
      expect(find.text('Assigned Ride'), findsOneWidget);
      expect(find.text('Requests'), findsOneWidget);
      expect(find.text('Trip'), findsOneWidget);
      expect(find.text('Replay'), findsOneWidget);
      expect(find.text('Earnings'), findsOneWidget);
      expect(fakeClient.assignedRideCalls, 1);

      await tester.tap(find.text('Trip'));
      await tester.pumpAndSettle();

      expect(find.text('Trip Lifecycle'), findsOneWidget);
      expect(find.text('Assigned Trip'), findsOneWidget);
      expect(find.text('Assignment: Verified'), findsWidgets);

      await tester.tap(find.text('Replay'));
      await tester.pumpAndSettle();

      expect(fakeClient.replayCalls, 1);
      expect(find.text('Replay Evidence'), findsWidgets);
      expect(find.text('Replay: Verified'), findsOneWidget);
      expect(find.text('Replay Hash: hash-1'), findsOneWidget);

      await tester.tap(find.text('Earnings'));
      await tester.pumpAndSettle();

      expect(fakeClient.earningsCalls, 1);
      expect(find.text('Earnings Evidence'), findsOneWidget);
      expect(find.text('Driver ID: driver-1'), findsOneWidget);
      expect(find.text('Daily Total: 50.00'), findsOneWidget);
      expect(find.text('Weekly Total: 300.00'), findsOneWidget);
    },
  );

  testWidgets(
    'driver app shell keeps lifecycle actions API-bound',
    (tester) async {
      final fakeClient = FakeMainAppHttpClient();

      final apiClient = AfriRideApiClient(
        baseUrl: 'https://example.invalid',
        client: fakeClient,
      );

      await tester.pumpWidget(
        AfriRideDriverApp(
          driverId: 'driver-1',
          apiClient: apiClient,
        ),
      );

      await tester.pumpAndSettle();

      await tester.tap(find.text('Trip'));
      await tester.pumpAndSettle();

      await tester.tap(find.text('Start Ride'));
      await tester.pumpAndSettle();

      expect(fakeClient.startCalls, 1);

      await tester.tap(find.text('Complete Ride'));
      await tester.pumpAndSettle();

      expect(fakeClient.completeCalls, 1);
    },
  );
}