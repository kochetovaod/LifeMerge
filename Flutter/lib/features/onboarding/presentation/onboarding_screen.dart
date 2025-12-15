import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../core/routing/routes.dart';

class OnboardingScreen extends StatelessWidget {
  const OnboardingScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Onboarding')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            const Text('Onboarding placeholder'),
            const SizedBox(height: 16),
            FilledButton(
              onPressed: () => context.go(Routes.calendarDay),
              child: const Text('Finish onboarding'),
            ),
          ],
        ),
      ),
    );
  }
}
