import 'dart:developer';

import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Lightweight analytics service that wraps future integrations
/// (e.g., Firebase Analytics). For now it simply logs events.
class AnalyticsService {
  const AnalyticsService();

  Future<void> logEvent(String name, {Map<String, dynamic>? parameters}) async {
    log('Analytics event: $name ${parameters ?? {}}');
  }
}

/// Global provider for the analytics service.
final analyticsProvider = Provider<AnalyticsService>((ref) {
  return const AnalyticsService();
});
