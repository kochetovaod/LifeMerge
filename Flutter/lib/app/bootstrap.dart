import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../core/di/providers.dart';
import '../features/auth/application/auth_controller.dart';

Future<ProviderContainer> bootstrap() async {
  final prefs = await SharedPreferences.getInstance();

  final container = ProviderContainer(
    overrides: <Override>[
      sharedPreferencesProvider.overrideWithValue(prefs),
    ],
  );

  await container.read(authControllerProvider.notifier).restoreSession();
  return container;
}
