import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:afriride_driver_pilot/contracts/earnings_contract.dart';
import 'package:afriride_driver_pilot/guards/driver_evidence_guard.dart';
import 'package:afriride_driver_pilot/widgets/earnings_tile.dart';

void main() {
  testWidgets(
    "renders valid earnings evidence",
    (tester) async {
      final earnings = EarningsContract(
        driverId: "driver-1",
        dailyTotal: 50,
        weeklyTotal: 300,
        earningsReceiptId: "earnings-receipt-1",
        earningsPeriodId: "period-1",
        replayVerified: true,
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: EarningsTile(
              earnings: earnings,
            ),
          ),
        ),
      );

      expect(
        find.text("Earnings Evidence"),
        findsOneWidget,
      );
      expect(
        find.text("Driver ID: driver-1"),
        findsOneWidget,
      );
      expect(
        find.text("Daily Total: 50.00"),
        findsOneWidget,
      );
      expect(
        find.text("Weekly Total: 300.00"),
        findsOneWidget,
      );
      expect(
        find.text("Replay: Verified"),
        findsOneWidget,
      );
      expect(
        find.text("Receipt Evidence: earnings-receipt-1"),
        findsOneWidget,
      );
      expect(
        find.text("Period Evidence: period-1"),
        findsOneWidget,
      );
    },
  );

  testWidgets(
    "rejects negative earnings before rendering",
    (tester) async {
      final earnings = EarningsContract(
        driverId: "driver-1",
        dailyTotal: -1,
        weeklyTotal: 300,
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

  testWidgets(
    "renders unverified replay badge when replay evidence is not verified",
    (tester) async {
      final earnings = EarningsContract(
        driverId: "driver-1",
        dailyTotal: 50,
        weeklyTotal: 300,
        replayVerified: false,
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: EarningsTile(
              earnings: earnings,
            ),
          ),
        ),
      );

      expect(
        find.text("Replay: Not verified"),
        findsOneWidget,
      );
    },
  );
}