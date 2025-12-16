import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../data/datasources/local/tasks_cache.dart';
import '../../data/datasources/remote/api_client.dart';
import '../../data/datasources/remote/calendar_api_service.dart';
import '../../data/repositories/auth_repository_impl.dart';
import '../../data/repositories/calendar_repository_impl.dart';
import '../../data/repositories/in_memory_inbox_repository.dart';
import '../../data/repositories/tasks_repository_impl.dart';
import '../../domain/repositories/auth_repository.dart';
import '../../domain/repositories/calendar_repository.dart';
import '../../domain/repositories/inbox_repository.dart';
import '../../domain/repositories/tasks_repository.dart';

final sharedPreferencesProvider = Provider<SharedPreferences>((ref) {
  throw UnimplementedError('SharedPreferences must be provided during bootstrap');
});

final dioProvider = Provider<Dio>((ref) {
  return Dio(
    BaseOptions(
      baseUrl: 'http://localhost:8000/v1',
      connectTimeout: const Duration(seconds: 30),
      receiveTimeout: const Duration(seconds: 30),
    ),
  );
});

final apiClientProvider = Provider<ApiClient>((ref) {
  return ApiClient(ref.read(dioProvider));
});

final authRepositoryProvider = Provider<AuthRepository>((ref) {
  return AuthRepositoryImpl(
    ref.read(apiClientProvider),
    ref.read(sharedPreferencesProvider),
  );
});

final tasksCacheProvider = Provider<TasksCache>((ref) {
  return TasksCache(ref.read(sharedPreferencesProvider));
});

final tasksRepositoryProvider = Provider<TasksRepository>((ref) {
  return TasksRepositoryImpl(
    ref.read(apiClientProvider),
    ref.read(tasksCacheProvider),
  );
});

final calendarApiServiceProvider = Provider<CalendarApiService>((ref) {
  return CalendarApiService();
});

final calendarRepositoryProvider = Provider<CalendarRepository>((ref) {
  return CalendarRepositoryImpl(ref.read(calendarApiServiceProvider));
});

final inboxRepositoryProvider = Provider<InboxRepository>((ref) {
  return InMemoryInboxRepository();
});

