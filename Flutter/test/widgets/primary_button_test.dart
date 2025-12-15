import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:lifemerge/features/auth/presentation/widgets/primary_button.dart';

void main() {
  group('PrimaryButton', () {
    testWidgets('renders label and triggers callback when enabled', (tester) async {
      var pressed = false;

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: PrimaryButton(
              label: 'Continue',
              onPressed: () {
                pressed = true;
              },
            ),
          ),
        ),
      );

      expect(find.text('Continue'), findsOneWidget);

      await tester.tap(find.byType(PrimaryButton));
      await tester.pumpAndSettle();

      expect(pressed, isTrue);
    });

    testWidgets('shows loader and disables tap when loading', (tester) async {
      var pressed = false;

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: PrimaryButton(
              label: 'Loading',
              isLoading: true,
              onPressed: () {
                pressed = true;
              },
            ),
          ),
        ),
      );

      expect(find.byType(CircularProgressIndicator), findsOneWidget);
      await tester.tap(find.byType(PrimaryButton));
      await tester.pumpAndSettle();

      expect(pressed, isFalse);
    });
  });
}
