import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

import 'package:afriride_driver_pilot/api/afriride_api_client.dart';
import 'package:afriride_driver_pilot/screens/ride_requests_screen.dart';

class FakeRideAcceptanceHttpClient extends http.BaseClient {
  int acceptCalls = 0;
  int rejectCalls = 0;

  @override
  Future<http.StreamedResponse> send(
    http.BaseRequest request,
  ) async {
    final path = request.url.path;

    if (request.method == "GET" &&
        path == "/driver/driver-1/rides/assigned") {
      return _jsonResponse(
        {
          "rides": [
            {
              "ride_id": "ride-1",
              "pickup": "Pickup A",
              "dropoff": "Dropoff B",
              "status": "assigned",
              "assigned_driver_id": "driver-1",
            },
          ],
        },
      );
    }

    if (request.method == "POST" &&
        path == "/ride/ride-1/accept") {
      acceptCalls += 1;
      return _jsonResponse({"ok": true});
    }

    if (request.method == "POST" &&
        path == "/ride/ride-1/reject") {
      rejectCalls += 1;
      return _jsonResponse({"ok": true});
    }

    return _jsonResponse(
      {"error": "not_found"},
      statusCode: 404,
    );
  }

  http.StreamedResponse _jsonResponse(
    Map<String, dynamic> body, {
    int statusCode = 200,
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
    "driver accepts assigned ride through API contract",
    (tester) async {
      final fakeClient = FakeRideAcceptanceHttpClient();

      final apiClient = AfriRideApiClient(
        baseUrl: "https://example.invalid",
        client: fakeClient,
      );

      await tester.pumpWidget(
        MaterialApp(
          home: RideRequestsScreen(
            driverId: "driver-1",
            apiClient: apiClient,
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text("Ride Requests"), findsOneWidget);
      expect(find.text("Assigned Ride"), findsOneWidget);
      expect(find.text("Pickup: Pickup A"), findsOneWidget);
      expect(find.text("Dropoff: Dropoff B"), findsOneWidget);
      expect(find.text("Assignment: Verified"), findsOneWidget);

      await tester.tap(find.text("Accept"));
      await tester.pumpAndSettle();

      expect(fakeClient.acceptCalls, 1);
      expect(fakeClient.rejectCalls, 0);
    },
  );

  testWidgets(
    "driver rejection remains API-bound and does not create dispatch authority",
    (tester) async {
      final fakeClient = FakeRideAcceptanceHttpClient();

      final apiClient = AfriRideApiClient(
        baseUrl: "https://example.invalid",
        client: fakeClient,
      );

      await tester.pumpWidget(
        MaterialApp(
          home: RideRequestsScreen(
            driverId: "driver-1",
            apiClient: apiClient,
          ),
        ),
      );

      await tester.pumpAndSettle();

      await tester.tap(find.text("Reject"));
      await tester.pumpAndSettle();

      expect(fakeClient.rejectCalls, 1);
      expect(fakeClient.acceptCalls, 0);
    },
  );
}