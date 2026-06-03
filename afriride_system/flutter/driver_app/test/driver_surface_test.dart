import 'package:flutter_test/flutter_test.dart';

import 'package:afriride_driver_pilot/api/afriride_api_client.dart';
import 'package:afriride_driver_pilot/contracts/earnings_contract.dart';
import 'package:afriride_driver_pilot/contracts/receipt_contract.dart';
import 'package:afriride_driver_pilot/contracts/replay_contract.dart';
import 'package:afriride_driver_pilot/contracts/ride_contract.dart';
import 'package:afriride_driver_pilot/guards/driver_evidence_guard.dart';

void main() {
  group(
    "Driver App surface boundary",
    () {
      test(
        "ride contract carries assigned ride evidence only",
        () {
          final ride = RideContract(
            rideId: "ride-1",
            pickup: "Pickup A",
            dropoff: "Dropoff B",
            status: RideStatus.assigned,
            assignedDriverId: "driver-1",
          );

          expect(ride.rideId, "ride-1");
          expect(ride.assignedDriverId, "driver-1");
          expect(ride.status, RideStatus.assigned);
        },
      );

      test(
        "replay contract carries replay evidence only",
        () {
          final replay = ReplayContract(
            rideId: "ride-1",
            replayId: "replay-1",
            replayVerified: true,
          );

          expect(replay.rideId, "ride-1");
          expect(replay.replayId, "replay-1");
          expect(replay.replayVerified, true);
        },
      );

      test(
        "receipt contract carries receipt evidence only",
        () {
          final receipt = ReceiptContract(
            rideId: "ride-1",
            receiptId: "receipt-1",
            status: "completed",
          );

          expect(receipt.rideId, "ride-1");
          expect(receipt.receiptId, "receipt-1");
          expect(receipt.status, "completed");
        },
      );

      test(
        "earnings contract carries earnings evidence only",
        () {
          final earnings = EarningsContract(
            driverId: "driver-1",
            dailyTotal: 50,
            weeklyTotal: 300,
          );

          expect(earnings.driverId, "driver-1");
          expect(earnings.dailyTotal, 50);
          expect(earnings.weeklyTotal, 300);
        },
      );

      test(
        "driver evidence guard accepts valid assigned ride",
        () {
          final ride = RideContract(
            rideId: "ride-1",
            pickup: "Pickup A",
            dropoff: "Dropoff B",
            status: RideStatus.assigned,
            assignedDriverId: "driver-1",
          );

          expect(
            () => DriverEvidenceGuard.validateDriverAssignment(
              ride,
              "driver-1",
            ),
            returnsNormally,
          );
        },
      );

      test(
        "API client fails closed without injected HTTP client",
        () async {
          final api = AfriRideApiClient(
            baseUrl: "https://example.invalid",
          );

          expect(
            () => api.getAssignedRideRequests(
              driverId: "driver-1",
            ),
            throwsA(
              isA<ApiContractException>(),
            ),
          );
        },
      );
    },
  );
}