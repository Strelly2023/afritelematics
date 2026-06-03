import 'package:flutter_test/flutter_test.dart';

import 'package:afriride_driver_pilot/contracts/earnings_contract.dart';
import 'package:afriride_driver_pilot/contracts/receipt_contract.dart';
import 'package:afriride_driver_pilot/contracts/replay_contract.dart';
import 'package:afriride_driver_pilot/contracts/ride_contract.dart';

void main() {
  group(
    "RideContract",
    () {
      test(
        "parses valid payload",
        () {
          final ride = RideContract.fromJson(
            {
              "ride_id": "ride-1",
              "pickup": "A",
              "dropoff": "B",
              "status": "assigned",
              "assigned_driver_id":
                  "driver-1",
            },
          );

          expect(
            ride.rideId,
            "ride-1",
          );

          expect(
            ride.assignedDriverId,
            "driver-1",
          );

          expect(
            ride.status,
            RideStatus.assigned,
          );
        },
      );

      test(
        "rejects missing ride id",
        () {
          expect(
            () => RideContract.fromJson(
              {
                "ride_id": "",
                "pickup": "A",
                "dropoff": "B",
                "status": "assigned",
                "assigned_driver_id":
                    "driver-1",
              },
            ),
            throwsArgumentError,
          );
        },
      );

      test(
        "supports deterministic json",
        () {
          final ride = RideContract(
            rideId: "ride-1",
            pickup: "A",
            dropoff: "B",
            status: RideStatus.assigned,
            assignedDriverId:
                "driver-1",
          );

          final json = ride.toJson();

          expect(
            json["ride_id"],
            "ride-1",
          );
        },
      );
    },
  );

  group(
    "ReplayContract",
    () {
      test(
        "parses valid replay",
        () {
          final replay =
              ReplayContract.fromJson(
            {
              "ride_id": "ride-1",
              "replay_id":
                  "replay-1",
              "replay_verified":
                  true,
            },
          );

          expect(
            replay.replayVerified,
            true,
          );
        },
      );

      test(
        "rejects missing replay id",
        () {
          expect(
            () => ReplayContract
                .fromJson(
              {
                "ride_id":
                    "ride-1",
                "replay_id": "",
                "replay_verified":
                    true,
              },
            ),
            throwsArgumentError,
          );
        },
      );

      test(
        "serializes replay",
        () {
          final replay =
              ReplayContract(
            rideId: "ride-1",
            replayId:
                "replay-1",
            replayVerified:
                true,
          );

          expect(
            replay.toJson()[
                "replay_id"],
            "replay-1",
          );
        },
      );
    },
  );

  group(
    "ReceiptContract",
    () {
      test(
        "parses valid receipt",
        () {
          final receipt =
              ReceiptContract
                  .fromJson(
            {
              "ride_id":
                  "ride-1",
              "receipt_id":
                  "receipt-1",
              "status":
                  "completed",
            },
          );

          expect(
            receipt.receiptId,
            "receipt-1",
          );
        },
      );

      test(
        "rejects missing receipt id",
        () {
          expect(
            () =>
                ReceiptContract
                    .fromJson(
              {
                "ride_id":
                    "ride-1",
                "receipt_id":
                    "",
                "status":
                    "completed",
              },
            ),
            throwsArgumentError,
          );
        },
      );

      test(
        "serializes receipt",
        () {
          final receipt =
              ReceiptContract(
            rideId: "ride-1",
            receiptId:
                "receipt-1",
            status:
                "completed",
          );

          expect(
            receipt.toJson()[
                "receipt_id"],
            "receipt-1",
          );
        },
      );
    },
  );

  group(
    "EarningsContract",
    () {
      test(
        "parses valid earnings",
        () {
          final earnings =
              EarningsContract
                  .fromJson(
            {
              "driver_id":
                  "driver-1",
              "daily_total":
                  50.0,
              "weekly_total":
                  300.0,
            },
          );

          expect(
            earnings.dailyTotal,
            50,
          );

          expect(
            earnings.weeklyTotal,
            300,
          );
        },
      );

      test(
        "rejects negative daily total",
        () {
          expect(
            () =>
                EarningsContract
                    .fromJson(
              {
                "driver_id":
                    "driver-1",
                "daily_total":
                    -1,
                "weekly_total":
                    100,
              },
            ),
            throwsArgumentError,
          );
        },
      );

      test(
        "serializes earnings",
        () {
          final earnings =
              EarningsContract(
            driverId:
                "driver-1",
            dailyTotal: 10,
            weeklyTotal:
                100,
          );

          expect(
            earnings.toJson()[
                "driver_id"],
            "driver-1",
          );
        },
      );
    },
  );
}