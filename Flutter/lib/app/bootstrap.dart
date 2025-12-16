import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../data/datasources/remote/interceptors.dart';
import '../presentation/providers/presentation_providers.dart';
import 'di/providers.dart';

Future<ProviderContainer> bootstrap() async {
  final prefs = await SharedPreferences.getInstance();

  final container = ProviderContainer(
    overrides: <Override>[
      sharedPreferencesProvider.overrideWithValue(prefs),
    ],
  );

  final dio = container.read(dioProvider);
  final authNotifier = container.read(authControllerProvider.notifier);
  dio.interceptors.add(
    AuthInterceptor(
      authRepository: container.read(authRepositoryProvider),
      dio: dio,
      onUnauthorized: () => authNotifier.signOut(),
    ),
  );

  await authNotifier.restoreSession();
  return container;
}
