import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

import 'package:afriride_driver_pilot/api/afriride_api_client.dart';
import 'package:afriride_driver_pilot/contracts/ride_contract.dart';
import 'package:afriride_driver_pilot/screens/trip_lifecycle_screen.dart';

class FakeTripCompletionHttpClient extends http.BaseClient {
  int startCalls = 0;
  int completeCalls = 0;

  @override
  Future<http.StreamedResponse> send(
    http.BaseRequest request,
  ) async {
    final path = request.url.path;

    if (request.method == "POST" &&
        path == "/ride/ride-1/start") {
      startCalls += 1;
      return _jsonResponse({"ok": true});
    }

    if (request.method == "POST" &&
        path == "/ride/ride-1/complete") {
      completeCalls += 1;
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
    "driver starts and completes trip through API contract",
    (tester) async {
      final fakeClient = FakeTripCompletionHttpClient();

      final apiClient = AfriRideApiClient(
        baseUrl: "https://example.invalid",
        client: fakeClient,
      );

      final acceptedRide = RideContract(
        rideId: "ride-1",
        pickup: "Pickup A",
        dropoff: "Dropoff B",
        status: RideStatus.accepted,
        assignedDriverId: "driver-1",
      );

      await tester.pumpWidget(
        MaterialApp(
          home: TripLifecycleScreen(
            driverId: "driver-1",
            ride: acceptedRide,
            apiClient: apiClient,
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text("Trip Lifecycle"), findsOneWidget);
      expect(find.text("Assigned Trip"), findsOneWidget);
      expect(find.text("Assignment: Verified"), findsOneWidget);

      await tester.tap(find.text("Start Ride"));
      await tester.pumpAndSettle();

      expect(fakeClient.startCalls, 1);
      expect(fakeClient.completeCalls, 0);

      final activeRide = RideContract(
        rideId: "ride-1",
        pickup: "Pickup A",
        dropoff: "Dropoff B",
        status: RideStatus.inProgress,
        assignedDriverId: "driver-1",
      );

      await tester.pumpWidget(
        MaterialApp(
          home: TripLifecycleScreen(
            driverId: "driver-1",
            ride: activeRide,
            apiClient: apiClient,
          ),
        ),
      );

      await tester.pumpAndSettle();

      await tester.tap(find.text("Complete Ride"));
      await tester.pumpAndSettle();

      expect(fakeClient.startCalls, 1);
      expect(fakeClient.completeCalls, 1);
    },
  );

  testWidgets(
    "trip lifecycle rejects mismatched driver assignment",
    (tester) async {
      final fakeClient = FakeTripCompletionHttpClient();

      final apiClient = AfriRideApiClient(
        baseUrl: "https://example.invalid",
        client: fakeClient,
      );

      final mismatchedRide = RideContract(
        rideId: "ride-1",
        pickup: "Pickup A",
        dropoff: "Dropoff B",
        status: RideStatus.accepted,
        assignedDriverId: "driver-2",
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Builder(
            builder: (_) {
              expect(
                () => TripLifecycleScreen(
                  driverId: "driver-1",
                  ride: mismatchedRide,
                  apiClient: apiClient,
                ),
                returnsNormally,
              );

              return const SizedBox.shrink();
            },
          ),
        ),
      );

      expect(fakeClient.startCalls, 0);
      expect(fakeClient.completeCalls, 0);
    },
  );
}

 