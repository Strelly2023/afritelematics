import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:afriride_driver_pilot/widgets/evidence_badge.dart';

void main() {
  testWidgets(
    "renders verified evidence badge",
    (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: EvidenceBadge(
              label: "Replay",
              verified: true,
            ),
          ),
        ),
      );

      expect(find.text("Replay: Verified"), findsOneWidget);
    },
  );

  testWidgets(
    "renders unverified evidence badge",
    (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: EvidenceBadge(
              label: "Replay",
              verified: false,
            ),
          ),
        ),
      );

      expect(find.text("Replay: Not verified"), findsOneWidget);
    },
  );
}