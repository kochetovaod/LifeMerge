import 'dart:async';

import 'package:dio/dio.dart';
import 'package:uuid/uuid.dart';

import '../../../domain/repositories/auth_repository.dart';

class AuthInterceptor extends Interceptor {
  AuthInterceptor({
    required AuthRepository authRepository,
    required Dio dio,
    required Future<void> Function() onUnauthorized,
  })  : _authRepository = authRepository,
        _dio = dio,
        _onUnauthorized = onUnauthorized;

  final AuthRepository _authRepository;
  final Dio _dio;
  final Future<void> Function() _onUnauthorized;

  Completer<bool>? _refreshCompleter;

  @override
  Future<void> onRequest(RequestOptions options, RequestInterceptorHandler handler) async {
    options.headers['X-Request-Id'] ??= const Uuid().v4();
    options.headers['X-Timezone'] ??= 'UTC';

    final token = await _authRepository.getAccessToken();
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }

    handler.next(options);
  }

  @override
  Future<void> onError(DioException err, ErrorInterceptorHandler handler) async {
    final status = err.response?.statusCode;
    final is401 = status == 401;
    final isRefreshCall = err.requestOptions.path.contains('/auth/refresh');

    if (!is401 || isRefreshCall) {
      handler.next(err);
      return;
    }

    final refreshed = await _refreshOnce();
    if (!refreshed) {
      await _onUnauthorized();
      handler.next(err);
      return;
    }

    final newToken = await _authRepository.getAccessToken();
    final retryOptions = err.requestOptions;
    if (newToken != null) {
      retryOptions.headers['Authorization'] = 'Bearer $newToken';
    }

    try {
      final response = await _dio.fetch<dynamic>(retryOptions);
      handler.resolve(response);
    } catch (_) {
      handler.next(err);
    }
  }

  Future<bool> _refreshOnce() async {
    if (_refreshCompleter != null) {
      return _refreshCompleter!.future;
    }

    _refreshCompleter = Completer<bool>();
    try {
      final ok = await _authRepository.refreshAccessToken();
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
