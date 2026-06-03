import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:afriride_driver_pilot/contracts/ride_contract.dart';
import 'package:afriride_driver_pilot/guards/driver_evidence_guard.dart';
import 'package:afriride_driver_pilot/widgets/ride_card.dart';

void main() {
  testWidgets(
    "renders assigned ride evidence",
    (tester) async {
      final ride = RideContract(
        rideId: "ride-1",
        pickup: "Pickup A",
        dropoff: "Dropoff B",
        status: RideStatus.assigned,
        assignedDriverId: "driver-1",
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: RideCard(
              ride: ride,
              driverId: "driver-1",
            ),
          ),
        ),
      );

      expect(find.text("Assigned Ride"), findsOneWidget);
      expect(find.text("Pickup: Pickup A"), findsOneWidget);
      expect(find.text("Dropoff: Dropoff B"), findsOneWidget);
      expect(find.text("Assignment: Verified"), findsOneWidget);
    },
  );

  testWidgets(
    "rejects ride assigned to different driver",
    (tester) async {
      final ride = RideContract(
        rideId: "ride-1",
        pickup: "Pickup A",
        dropoff: "Dropoff B",
        status: RideStatus.assigned,
        assignedDriverId: "driver-1",
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Builder(
              builder: (_) {
                expect(
                  () => DriverEvidenceGuard
                      .validateDriverAssignment(
                    ride,
                    "driver-2",
                  ),
                  throwsA(
                    isA<DriverEvidenceException>(),
                  ),
                );

                return const SizedBox.shrink();
              },
            ),
          ),
        ),
      );
    },
  );

  testWidgets(
    "accept callback is delegated",
    (tester) async {
      var accepted = false;

      final ride = RideContract(
        rideId: "ride-1",
        pickup: "Pickup A",
        dropoff: "Dropoff B",
        status: RideStatus.assigned,
        assignedDriverId: "driver-1",
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: RideCard(
              ride: ride,
              driverId: "driver-1",
              onAccept: () {
                accepted = true;
              },
            ),
          ),
        ),
      );

      await tester.tap(find.text("Accept"));
      await tester.pump();

      expect(accepted, true);
    },
  );

  testWidgets(
    "reject callback is delegated",
    (tester) async {
      var rejected = false;

      final ride = RideContract(
        rideId: "ride-1",
        pickup: "Pickup A",
        dropoff: "Dropoff B",
        status: RideStatus.assigned,
        assignedDriverId: "driver-1",
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: RideCard(
              ride: ride,
              driverId: "driver-1",
              onReject: () {
                rejected = true;
              },
            ),
          ),
        ),
      );

      await tester.tap(find.text("Reject"));
      await tester.pump();

      expect(rejected, true);
    },
  );
}