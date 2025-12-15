// lib/core/di/providers.dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../network/api_client.dart';
import '../network/interceptors.dart';
import '../../features/auth/data/auth_repository.dart';
import '../../features/auth/application/auth_controller.dart';
import '../../features/tasks/data/tasks_repository.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import '../../features/tasks/application/tasks_controller.dart';
import '../../features/tasks/application/tasks_state.dart';
import '../../features/tasks/data/tasks_cache.dart';

// Глобальные провайдеры
final sharedPreferencesProvider = Provider<SharedPreferences>((ref) {
  throw UnimplementedError('SharedPreferences должен быть переопределен в main');
});

final dioProvider = Provider<Dio>((ref) {
  final dio = Dio(BaseOptions(
    baseUrl: 'http://localhost:8000/v1', // Измените на ваш URL
    connectTimeout: const Duration(seconds: 30),
    receiveTimeout: const Duration(seconds: 30),
  ));
  
  dio.interceptors.addAll([
    AuthInterceptor(ref),
    LogInterceptor(requestBody: true, responseBody: true),
  ]);
  
  return dio;
});

final apiClientProvider = Provider<ApiClient>((ref) {
  return ApiClient(ref.read(dioProvider));
});

// Репозитории
final authRepositoryProvider = Provider<AuthRepository>((ref) {
  return AuthRepository(
    ref.read(apiClientProvider),
    ref.read(sharedPreferencesProvider),
  );
});

final tasksRepositoryProvider = Provider<TasksRepository>((ref) {
  return TasksRepository(ref.read(apiClientProvider));
});

// Контроллеры
final authControllerProvider = StateNotifierProvider<AuthController, AuthState>(
  (ref) => AuthController(ref.read(authRepositoryProvider)),
);

// Глобальное состояние
final isAuthenticatedProvider = Provider<bool>((ref) {
  final authState = ref.watch(authControllerProvider);
  return authState is AuthenticatedAuthState;
});

final currentUserProvider = Provider<User?>((ref) {
  final authState = ref.watch(authControllerProvider);
  if (authState is AuthenticatedAuthState) {
    return authState.user;
  }
  return null;
});

// Добавляем в providers.dart
final syncServiceProvider = Provider<SyncService>((ref) {
  return SyncService(ref.read(apiClientProvider));
});

final connectivityProvider = StreamProvider<ConnectivityResult>((ref) {
  return Connectivity().onConnectivityChanged;
});

// Провайдер для отслеживания состояния сети
final isOnlineProvider = Provider<bool>((ref) {
  final connectivity = ref.watch(connectivityProvider);
  return connectivity.value != ConnectivityResult.none;
});

final tasksCacheProvider = Provider<TasksCache>((ref) {
  return TasksCache(ref.read(sharedPreferencesProvider));
});

final tasksControllerProvider = StateNotifierProvider<TasksController, TasksState>((ref) {
  return TasksController(
    ref.read(tasksRepositoryProvider),
    ref.read(tasksCacheProvider),
  );
});
