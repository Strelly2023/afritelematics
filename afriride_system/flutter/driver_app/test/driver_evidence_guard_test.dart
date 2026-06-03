import 'package:flutter_test/flutter_test.dart';

import 'package:afriride_driver_pilot/contracts/earnings_contract.dart';
import 'package:afriride_driver_pilot/contracts/receipt_contract.dart';
import 'package:afriride_driver_pilot/contracts/replay_contract.dart';
import 'package:afriride_driver_pilot/contracts/ride_contract.dart';
import 'package:afriride_driver_pilot/guards/driver_evidence_guard.dart';

void main() {
  group(
    "DriverEvidenceGuard replay validation",
    () {
      test(
        "reject unverified replay",
        () {
          final replay = ReplayContract(
            rideId: "ride-1",
            replayId: "replay-1",
            replayVerified: false,
          );

          expect(
            () => DriverEvidenceGuard.validateReplay(
              replay,
            ),
            throwsA(
              isA<DriverEvidenceException>(),
            ),
          );
        },
      );

      test(
        "accept verified replay",
        () {
          final replay = ReplayContract(
            rideId: "ride-1",
            replayId: "replay-1",
            replayVerified: true,
          );

          expect(
            () => DriverEvidenceGuard.validateReplay(
              replay,
            ),
            returnsNormally,
          );
        },
      );

      test(
        "reject missing replay id",
        () {
          final replay = ReplayContract(
            rideId: "ride-1",
            replayId: "",
            replayVerified: true,
          );

          expect(
            () => DriverEvidenceGuard.validateReplay(
              replay,
            ),
            throwsA(
              isA<DriverEvidenceException>(),
            ),
          );
        },
      );
    },
  );

  group(
    "DriverEvidenceGuard receipt validation",
    () {
      test(
        "reject missing receipt id",
        () {
          final receipt = ReceiptContract(
            rideId: "ride-1",
            receiptId: "",
            status: "completed",
          );

          expect(
            () => DriverEvidenceGuard.validateReceipt(
              receipt,
            ),
            throwsA(
              isA<DriverEvidenceException>(),
            ),
          );
        },
      );

      test(
        "accept valid receipt",
        () {
          final receipt = ReceiptContract(
            rideId: "ride-1",
            receiptId: "receipt-1",
            status: "completed",
          );

          expect(
            () => DriverEvidenceGuard.validateReceipt(
              receipt,
            ),
            returnsNormally,
          );
        },
      );

      test(
        "reject non-completed receipt for completed evidence",
        () {
          final receipt = ReceiptContract(
            rideId: "ride-1",
            receiptId: "receipt-1",
            status: "pending",
          );

          expect(
            () =>
                DriverEvidenceGuard.validateCompletedReceipt(
              receipt,
            ),
            throwsA(
              isA<DriverEvidenceException>(),
            ),
          );
        },
      );
    },
  );

  group(
    "DriverEvidenceGuard assignment validation",
    () {
      test(
        "reject driver assignment mismatch",
        () {
          final ride = RideContract(
            rideId: "ride-1",
            pickup: "A",
            dropoff: "B",
            status: RideStatus.assigned,
            assignedDriverId: "driver-123",
          );

          expect(
            () =>
                DriverEvidenceGuard.validateDriverAssignment(
              ride,
              "driver-999",
            ),
            throwsA(
              isA<DriverEvidenceException>(),
            ),
          );
        },
      );

      test(
        "accept matching driver assignment",
        () {
          final ride = RideContract(
            rideId: "ride-1",
            pickup: "A",
            dropoff: "B",
            status: RideStatus.assigned,
            assignedDriverId: "driver-123",
          );

          expect(
            () =>
                DriverEvidenceGuard.validateDriverAssignment(
              ride,
              "driver-123",
            ),
            returnsNormally,
          );
        },
      );
    },
  );

  group(
    "DriverEvidenceGuard earnings validation",
    () {
      test(
        "reject negative daily earnings",
        () {
          final earnings = EarningsContract(
            driverId: "driver-123",
            dailyTotal: -1,
            weeklyTotal: 100,
          );

          expect(
            () => DriverEvidenceGuard.validateEarnings(
              earnings,
            ),
            throwsA(
              isA<DriverEvidenceException>(),
            ),
          );
        },
      );

      test(
        "reject negative weekly earnings",
        () {
          final earnings = EarningsContract(
            driverId: "driver-123",
            dailyTotal: 20,
            weeklyTotal: -1,
          );

          expect(
            () => DriverEvidenceGuard.validateEarnings(
              earnings,
            ),
            throwsA(
              isA<DriverEvidenceException>(),
            ),
          );
        },
      );

      test(
        "accept valid earnings evidence",
        () {
          final earnings = EarningsContract(
            driverId: "driver-123",
            dailyTotal: 20,
            weeklyTotal: 100,
          );

          expect(
            () => DriverEvidenceGuard.validateEarnings(
              earnings,
            ),
            returnsNormally,
          );
        },
      );
    },
  );

  group(
    "DriverEvidenceGuard evidence binding validation",
    () {
      test(
        "reject ride receipt mismatch",
        () {
          final ride = RideContract(
            rideId: "ride-1",
            pickup: "A",
            dropoff: "B",
            status: RideStatus.completed,
            assignedDriverId: "driver-123",
          );

          final receipt = ReceiptContract(
            rideId: "ride-2",
            receiptId: "receipt-1",
            status: "completed",
          );

          expect(
            () =>
                DriverEvidenceGuard.validateRideReceiptBinding(
              ride,
              receipt,
            ),
            throwsA(
              isA<DriverEvidenceException>(),
            ),
          );
        },
      );

      test(
        "reject ride replay mismatch",
        () {
          final ride = RideContract(
            rideId: "ride-1",
            pickup: "A",
            dropoff: "B",
            status: RideStatus.completed,
            assignedDriverId: "driver-123",
          );

          final replay = ReplayContract(
            rideId: "ride-2",
            replayId: "replay-1",
            replayVerified: true,
          );

          expect(
            () =>
                DriverEvidenceGuard.validateRideReplayBinding(
              ride,
              replay,
            ),
            throwsA(
              isA<DriverEvidenceException>(),
            ),
          );
        },
      );

      test(
        "accept valid ride receipt binding",
        () {
          final ride = RideContract(
            rideId: "ride-1",
            pickup: "A",
            dropoff: "B",
            status: RideStatus.completed,
            assignedDriverId: "driver-123",
          );

          final receipt = ReceiptContract(
            rideId: "ride-1",
            receiptId: "receipt-1",
            status: "completed",
          );

          expect(
            () =>
                DriverEvidenceGuard.validateRideReceiptBinding(
              ride,
              receipt,
            ),
            returnsNormally,
          );
        },
      );

      test(
        "accept valid ride replay binding",
        () {
          final ride = RideContract(
            rideId: "ride-1",
            pickup: "A",
            dropoff: "B",
            status: RideStatus.completed,
            assignedDriverId: "driver-123",
          );

          final replay = ReplayContract(
            rideId: "ride-1",
            replayId: "replay-1",
            replayVerified: true,
          );

          expect(
            () =>
                DriverEvidenceGuard.validateRideReplayBinding(
              ride,
              replay,
            ),
            returnsNormally,
          );
        },
      );
    },
  );
}