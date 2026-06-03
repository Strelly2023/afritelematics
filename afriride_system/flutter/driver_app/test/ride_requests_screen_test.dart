import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

import 'package:afriride_driver_pilot/api/afriride_api_client.dart';
import 'package:afriride_driver_pilot/screens/ride_requests_screen.dart';

class FakeHttpClient extends http.BaseClient {
  int acceptCalls = 0;
  int rejectCalls = 0;

  final List<Map<String, dynamic>> rides;

  FakeHttpClient({
    required this.rides,
  });

  @override
  Future<http.StreamedResponse> send(
    http.BaseRequest request,
  ) async {
    final path = request.url.path;

    if (request.method == "GET" &&
        path == "/driver/driver-1/rides/assigned") {
      return _jsonResponse(
        {
          "rides": rides,
        },
      );
    }

    if (request.method == "POST" &&
        path == "/ride/ride-1/accept") {
      acceptCalls += 1;
      return _jsonResponse(
        {
          "ok": true,
        },
      );
    }

    if (request.method == "POST" &&
        path == "/ride/ride-1/reject") {
      rejectCalls += 1;
      return _jsonResponse(
        {
          "ok": true,
        },
      );
    }

    return _jsonResponse(
      {
        "error": "not_found",
      },
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
          utf8.encode(jsonEncode(body)),
        ],
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
    "renders assigned ride requests",
    (tester) async {
      final client = FakeHttpClient(
        rides: [
          {
            "ride_id": "ride-1",
            "pickup": "Pickup A",
            "dropoff": "Dropoff B",
            "status": "assigned",
            "assigned_driver_id": "driver-1",
          },
        ],
      );

      await tester.pumpWidget(
        MaterialApp(
          home: RideRequestsScreen(
            driverId: "driver-1",
            apiClient: AfriRideApiClient(
              baseUrl: "https://example.invalid",
              client: client,
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text("Ride Requests"), findsOneWidget);
      expect(find.text("Assigned Ride"), findsOneWidget);
      expect(find.text("Pickup: Pickup A"), findsOneWidget);
      expect(find.text("Dropoff: Dropoff B"), findsOneWidget);
    },
  );

  testWidgets(
    "renders empty state when no assigned rides exist",
    (tester) async {
      final client = FakeHttpClient(
        rides: const [],
      );

      await tester.pumpWidget(
        MaterialApp(
          home: RideRequestsScreen(
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
        find.text("No assigned ride requests"),
        findsOneWidget,
      );
    },
  );

  testWidgets(
    "accept delegates to API contract",
    (tester) async {
      final client = FakeHttpClient(
        rides: [
          {
            "ride_id": "ride-1",
            "pickup": "Pickup A",
            "dropoff": "Dropoff B",
            "status": "assigned",
            "assigned_driver_id": "driver-1",
          },
        ],
      );

      await tester.pumpWidget(
        MaterialApp(
          home: RideRequestsScreen(
            driverId: "driver-1",
            apiClient: AfriRideApiClient(
              baseUrl: "https://example.invalid",
              client: client,
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      await tester.tap(find.text("Accept"));
      await tester.pumpAndSettle();

      expect(client.acceptCalls, 1);
    },
  );

  testWidgets(
    "reject delegates to API contract",
    (tester) async {
      final client = FakeHttpClient(
        rides: [
          {
            "ride_id": "ride-1",
            "pickup": "Pickup A",
            "dropoff": "Dropoff B",
            "status": "assigned",
            "assigned_driver_id": "driver-1",
          },
        ],
      );

      await tester.pumpWidget(
        MaterialApp(
          home: RideRequestsScreen(
            driverId: "driver-1",
            apiClient: AfriRideApiClient(
              baseUrl: "https://example.invalid",
              client: client,
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      await tester.tap(find.text("Reject"));
      await tester.pumpAndSettle();

      expect(client.rejectCalls, 1);
    },
  );

  testWidgets(
    "rejects ride assigned to another driver",
    (tester) async {
      final client = FakeHttpClient(
        rides: [
          {
            "ride_id": "ride-1",
            "pickup": "Pickup A",
            "dropoff": "Dropoff B",
            "status": "assigned",
            "assigned_driver_id": "driver-2",
          },
        ],
      );

      await tester.pumpWidget(
        MaterialApp(
          home: RideRequestsScreen(
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
        find.text("Unable to load ride requests"),
        findsOneWidget,
      );
      expect(
        find.textContaining("driver_assignment_mismatch"),
        findsOneWidget,
      );
    },
  );
}