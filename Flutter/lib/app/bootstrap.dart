import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../core/di/providers.dart';
import '../features/auth/application/auth_controller.dart';
import '../features/auth/data/session_storage.dart';

/// App bootstrap point.
///
/// Keep synchronous work minimal; do not perform feature initialization here.
Future<ProviderContainer> bootstrap() async {
  final prefs = await SharedPreferences.getInstance();
  final overrides = <Override>[
    ...appOverrides,
    sessionStorageProvider.overrideWithValue(SessionStorage(prefs)),
  ];

  final container = ProviderContainer(overrides: overrides);

  await container.read(authControllerProvider.notifier).restoreSession();

  // Placeholders for future: hydration, remote config, crash reporting initialization.
  return container;
}
