import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

import 'package:afriride_driver_pilot/api/afriride_api_client.dart';
import 'package:afriride_driver_pilot/screens/earnings_screen.dart';

class FakeEarningsHttpClient extends http.BaseClient {
  final Map<String, dynamic> responseBody;
  final int statusCode;

  FakeEarningsHttpClient({
    required this.responseBody,
    this.statusCode = 200,
  });

  @override
  Future<http.StreamedResponse> send(
    http.BaseRequest request,
  ) async {
    if (request.method == "GET" &&
        request.url.path == "/driver/driver-1/earnings") {
      return _jsonResponse(
        responseBody,
        statusCode: statusCode,
      );
    }

    return _jsonResponse(
      {"error": "not_found"},
      statusCode: 404,
    );
  }

  http.StreamedResponse _jsonResponse(
    Map<String, dynamic> body, {
    required int statusCode,
  }) {
    return http.StreamedResponse(
      Stream<List<int>>.fromIterable(
        [utf8.encode(jsonEncode(body))],
      ),
      statusCode,
      headers: {
        "content-type": "application/json",
      },
    );
  }
}

void main() {
  testWidgets(
    "renders earnings evidence",
    (tester) async {
      final client = FakeEarningsHttpClient(
        responseBody: {
          "driver_id": "driver-1",
          "daily_total": 50,
          "weekly_total": 300,
          "earnings_receipt_id": "earnings-receipt-1",
          "earnings_period_id": "period-1",
          "replay_verified": true,
        },
      );

      await tester.pumpWidget(
        MaterialApp(
          home: EarningsScreen(
            driverId: "driver-1",
            apiClient: AfriRideApiClient(
              baseUrl: "https://example.invalid",
              client: client,
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text("Earnings"), findsOneWidget);
      expect(find.text("Earnings Evidence"), findsOneWidget);
      expect(find.text("Driver ID: driver-1"), findsOneWidget);
      expect(find.text("Daily Total: 50.00"), findsOneWidget);
      expect(find.text("Weekly Total: 300.00"), findsOneWidget);
      expect(find.text("Replay: Verified"), findsOneWidget);
    },
  );

  testWidgets(
    "rejects earnings assigned to another driver",
    (tester) async {
      final client = FakeEarningsHttpClient(
        responseBody: {
          "driver_id": "driver-2",
          "daily_total": 50,
          "weekly_total": 300,
          "replay_verified": true,
        },
      );

      await tester.pumpWidget(
        MaterialApp(
          home: EarningsScreen(
            driverId: "driver-1",
            apiClient: AfriRideApiClient(
              baseUrl: "https://example.invalid",
              client: client,
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(
        find.text("Unable to load earnings evidence"),
        findsOneWidget,
      );
      expect(
        find.textContaining("earnings_driver_mismatch"),
        findsOneWidget,
      );
    },
  );

  testWidgets(
    "rejects negative earnings evidence",
    (tester) async {
      final client = FakeEarningsHttpClient(
        responseBody: {
          "driver_id": "driver-1",
          "daily_total": -1,
          "weekly_total": 300,
          "replay_verified": true,
        },
      );

      await tester.pumpWidget(
        MaterialApp(
          home: EarningsScreen(
            driverId: "driver-1",
            apiClient: AfriRideApiClient(
              baseUrl: "https://example.invalid",
              client: client,
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(
        find.text("Unable to load earnings evidence"),
        findsOneWidget,
      );
      expect(
        find.textContaining("negative_daily_total"),
        findsOneWidget,
      );
    },
  );

  testWidgets(
    "renders API failure state",
    (tester) async {
      final client = FakeEarningsHttpClient(
        responseBody: {
          "error": "server_error",
        },
        statusCode: 500,
      );

      await tester.pumpWidget(
        MaterialApp(
          home: EarningsScreen(
            driverId: "driver-1",
            apiClient: AfriRideApiClient(
              baseUrl: "https://example.invalid",
              client: client,
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(
        find.text("Unable to load earnings evidence"),
        findsOneWidget,
      );
      expect(
        find.textContaining("api_request_failed_500"),
        findsOneWidget,
      );
    },
  );
}