import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

import '../../domain/entities/auth/user.dart';
import '../../domain/repositories/auth_repository.dart';
import '../datasources/remote/api_client.dart';

class AuthRepositoryImpl implements AuthRepository {
  AuthRepositoryImpl(this._apiClient, this._prefs);

  final ApiClient _apiClient;
  final SharedPreferences _prefs;

  @override
  Future<String?> getAccessToken() async => _prefs.getString('access_token');

  @override
  Future<String?> getRefreshToken() async => _prefs.getString('refresh_token');

  @override
  Future<String> getDeviceId() async => _prefs.getString('device_id') ?? '';

  @override
  Future<User> signup({
    required String email,
    required String password,
    required String fullName,
    String timezone = 'UTC',
  }) async {
    final response = await _apiClient.signup(<String, dynamic>{
      'email': email,
      'password': password,
      'full_name': fullName,
      'timezone': timezone,
    });

    await _saveTokens(response);
    return User.fromJson(response['user'] as Map<String, dynamic>);
  }

  @override
  Future<User> login({
    required String email,
    required String password,
  }) async {
    final deviceId = await getDeviceId();
    final response = await _apiClient.login(<String, dynamic>{
      'email': email,
      'password': password,
      'device_id': deviceId,
    });

    await _saveTokens(response);
    return User.fromJson(response['user'] as Map<String, dynamic>);
  }

  @override
  Future<bool> refreshAccessToken() async {
    try {
      final refreshToken = await getRefreshToken();
      final deviceId = await getDeviceId();

      if (refreshToken == null) return false;

      final response = await _apiClient.refreshToken(<String, dynamic>{
        'refresh_token': refreshToken,
        'device_id': deviceId,
      });

      await _saveTokens(response);
      return true;
    } catch (_) {
      return false;
    }
  }

  @override
  Future<void> logout() async {
    final deviceId = await getDeviceId();
    final refreshToken = await getRefreshToken();

    if (refreshToken != null) {
      await _apiClient.logout(<String, dynamic>{
        'device_id': deviceId,
      });
    }

    await _clearTokens();
  }

  @override
  Future<bool> isAuthenticated() async {
    final token = await getAccessToken();
    return token != null;
  }

  @override
  Future<User?> getCurrentUser() async {
    final userJson = _prefs.getString('current_user');
    if (userJson == null) return null;

    try {
      final decoded = json.decode(userJson) as Map<String, dynamic>;
      return User.fromJson(decoded);
    } catch (_) {
      return null;
    }
  }

  Future<void> _saveTokens(Map<String, dynamic> response) async {
    await _prefs.setString('access_token', response['access_token'] as String);
    await _prefs.setString('refresh_token', response['refresh_token'] as String);

    final user = response['user'];
    if (user is Map<String, dynamic>) {
      await _prefs.setString('current_user', json.encode(user));
    }
  }

  Future<void> _clearTokens() async {
    await _prefs.remove('access_token');
    await _prefs.remove('refresh_token');
    await _prefs.remove('current_user');
  }
}
