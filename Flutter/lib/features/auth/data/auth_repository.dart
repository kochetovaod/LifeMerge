import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'auth_api_service.dart';
import 'session_storage.dart';

class AuthRepository {
  AuthRepository(this._api, this._storage);

  final AuthApiService _api;
  final SessionStorage _storage;

  Future<AuthSession> signUp({required String email, required String password}) async {
    final token = await _api.signUp(email: email, password: password);
    final session = AuthSession(email: email, token: token);
    await _storage.saveSession(session);
    return session;
  }

  Future<AuthSession> login({required String email, required String password}) async {
    final token = await _api.login(email: email, password: password);
    final session = AuthSession(email: email, token: token);
    await _storage.saveSession(session);
    return session;
  }

  Future<void> requestPasswordReset(String email) => _api.requestPasswordReset(email);

  Future<void> logout(String token) async {
    await _api.logout(token);
    await _storage.clear();
  }

  Future<AuthSession?> restore() => _storage.readSession();
}

class AuthSession {
  const AuthSession({required this.email, required this.token});

  final String email;
  final String token;
}

final authApiServiceProvider = Provider<AuthApiService>((ref) {
  return AuthApiService();
});

final authRepositoryProvider = Provider<AuthRepository>((ref) {
  final api = ref.read(authApiServiceProvider);
  final storage = ref.read(sessionStorageProvider);
  return AuthRepository(api, storage);
});
