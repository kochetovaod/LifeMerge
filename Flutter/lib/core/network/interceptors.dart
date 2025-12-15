import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:uuid/uuid.dart';

import '../di/providers.dart';

class AuthInterceptor extends Interceptor {
  AuthInterceptor(this.ref);

  final Ref ref;

  Completer<bool>? _refreshCompleter;

  @override
  Future<void> onRequest(RequestOptions options, RequestInterceptorHandler handler) async {
    final authRepo = ref.read(authRepositoryProvider);

    // request id для трассировки/идемпотентности (на бекенде это часто требуется)
    options.headers['X-Request-Id'] ??= const Uuid().v4();

    // timezone: лучше хранить IANA (Europe/Amsterdam), но пока хотя бы строка.
    options.headers['X-Timezone'] ??= 'UTC';

    final token = await authRepo.getAccessToken();
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }

    handler.next(options);
  }

  @override
  Future<void> onError(DioException err, ErrorInterceptorHandler handler) async {
    final status = err.response?.statusCode;
    final is401 = status == 401;

    // чтобы не уйти в цикл: refresh endpoint не рефрешим
    final isRefreshCall = err.requestOptions.path.contains('/auth/refresh');

    if (!is401 || isRefreshCall) {
      handler.next(err);
      return;
    }

    final refreshed = await _refreshOnce();
    if (!refreshed) {
      // токены протухли окончательно
      await ref.read(authControllerProvider.notifier).signOut();
      handler.next(err);
      return;
    }

    // повторяем исходный запрос с новым токеном
    final authRepo = ref.read(authRepositoryProvider);
    final newToken = await authRepo.getAccessToken();

    final retryOptions = err.requestOptions;
    if (newToken != null) {
      retryOptions.headers['Authorization'] = 'Bearer $newToken';
    }

    try {
      final response = await ref.read(dioProvider).fetch(retryOptions);
      handler.resolve(response);
    } catch (e) {
      handler.next(err);
    }
  }

  Future<bool> _refreshOnce() async {
    if (_refreshCompleter != null) {
      return _refreshCompleter!.future;
    }

    _refreshCompleter = Completer<bool>();
    try {
      final ok = await ref.read(authRepositoryProvider).refreshAccessToken();
      _refreshCompleter!.complete(ok);
      return ok;
    } catch (_) {
      _refreshCompleter!.complete(false);
      return false;
    } finally {
      _refreshCompleter = null;
    }
  }
}
