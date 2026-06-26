import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:afriride_driver_pilot/screens/verifier_screen.dart';
import 'package:afriride_driver_pilot/verifier/portable_receipt_verifier.dart';

void main() {
  test('portable verifier helper validates demo payload', () {
    final payload = buildDemoPrivacyQrPayload();
    final result = verifyPrivacyQrPayload(payload);

    expect(result.valid, true);
    expect(result.trustLevel, 'HIGH');
    expect(result.reason, 'stateless_verified');
    expect(result.zkReceipt, isNotNull);
    expect(result.bridge, isNotNull);
  });

  testWidgets('verifier screen renders and verifies demo payload', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: VerifierScreen(),
      ),
    );

    expect(find.text('Verifier'), findsOneWidget);
    expect(find.text('Load demo'), findsOneWidget);
    expect(find.text('Verify'), findsOneWidget);

    await tester.tap(find.text('Load demo'));
    await tester.pumpAndSettle();

    await tester.tap(find.text('Verify'));
    await tester.pumpAndSettle();

    expect(find.text('VERIFIED'), findsOneWidget);
    expect(find.text('Trust Level: HIGH'), findsOneWidget);
    expect(find.text('Reason: stateless_verified'), findsOneWidget);
  });
}
