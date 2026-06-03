import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

import 'package:afriride_driver_pilot/api/afriride_api_client.dart';
import 'package:afriride_driver_pilot/screens/replay_screen.dart';

class FakeReplayHttpClient extends http.BaseClient {
  final Map<String, dynamic> responseBody;
  final int statusCode;

  FakeReplayHttpClient({
    required this.responseBody,
    this.statusCode = 200,
  });

  @override
  Future<http.StreamedResponse> send(
    http.BaseRequest request,
  ) async {
    if (request.method == "GET" &&
        request.url.path == "/ride/ride-1/replay") {
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
    "renders replay evidence",
    (tester) async {
      final client = FakeReplayHttpClient(
        responseBody: {
          "ride_id": "ride-1",
          "replay_id": "replay-1",
          "replay_verified": true,
          "replay_hash": "hash-1",
          "receipt_id": "receipt-1",
          "replay_epoch": 1,
        },
      );

      await tester.pumpWidget(
        MaterialApp(
          home: ReplayScreen(
            rideId: "ride-1",
            apiClient: AfriRideApiClient(
              baseUrl: "https://example.invalid",
              client: client,
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text("Replay Evidence"), findsWidgets);
      expect(find.text("Ride ID: ride-1"), findsOneWidget);
      expect(find.text("Replay ID: replay-1"), findsOneWidget);
      expect(find.text("Replay: Verified"), findsOneWidget);
      expect(find.text("Replay Hash: hash-1"), findsOneWidget);
      expect(find.text("Receipt Binding: receipt-1"), findsOneWidget);
      expect(find.text("Replay Epoch: 1"), findsOneWidget);
    },
  );

  testWidgets(
    "rejects unverified replay evidence",
    (tester) async {
      final client = FakeReplayHttpClient(
        responseBody: {
          "ride_id": "ride-1",
          "replay_id": "replay-1",
          "replay_verified": false,
        },
      );

      await tester.pumpWidget(
        MaterialApp(
          home: ReplayScreen(
            rideId: "ride-1",
            apiClient: AfriRideApiClient(
              baseUrl: "https://example.invalid",
              client: client,
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(
        find.text("Unable to load replay evidence"),
        findsOneWidget,
      );
      expect(
        find.textContaining("replay_not_verified"),
        findsOneWidget,
      );
    },
  );

  testWidgets(
    "rejects replay for another ride",
    (tester) async {
      final client = FakeReplayHttpClient(
        responseBody: {
          "ride_id": "ride-2",
          "replay_id": "replay-1",
          "replay_verified": true,
        },
      );

      await tester.pumpWidget(
        MaterialApp(
          home: ReplayScreen(
            rideId: "ride-1",
            apiClient: AfriRideApiClient(
              baseUrl: "https://example.invalid",
              client: client,
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(
        find.text("Unable to load replay evidence"),
        findsOneWidget,
      );
      expect(
        find.textContaining("replay_ride_mismatch"),
        findsOneWidget,
      );
    },
  );

  testWidgets(
    "renders API failure state",
    (tester) async {
      final client = FakeReplayHttpClient(
        responseBody: {
          "error": "server_error",
        },
        statusCode: 500,
      );

      await tester.pumpWidget(
        MaterialApp(
          home: ReplayScreen(
            rideId: "ride-1",
            apiClient: AfriRideApiClient(
              baseUrl: "https://example.invalid",
              client: client,
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(
        find.text("Unable to load replay evidence"),
        findsOneWidget,
      );
      expect(
        find.textContaining("api_request_failed_500"),
        findsOneWidget,
      );
    },
  );
}