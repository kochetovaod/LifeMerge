import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import '../../../core/network/api_client.dart';
import '../../../domain/user.dart';

class AuthRepository {
  final ApiClient _apiClient;
  final SharedPreferences _prefs;

  AuthRepository(this._apiClient, this._prefs);

  Future<String?> getAccessToken() async {
    return _prefs.getString('access_token');
  }

  Future<String?> getRefreshToken() async {
    return _prefs.getString('refresh_token');
  }

  Future<String> getDeviceId() async {
    return _prefs.getString('device_id') ?? '';
  }

  Future<User> signup({
    required String email,
    required String password,
    required String fullName,
    String timezone = 'UTC',
  }) async {
    final response = await _apiClient.signup({
      'email': email,
      'password': password,
      'full_name': fullName,
      'timezone': timezone,
    });

    await _saveTokens(response);
    return User.fromJson(response['user']);
  }

  Future<User> login({
    required String email,
    required String password,
  }) async {
    final deviceId = await getDeviceId();
    final response = await _apiClient.login({
      'email': email,
      'password': password,
      'device_id': deviceId,
    });

    await _saveTokens(response);
    return User.fromJson(response['user']);
  }

  Future<bool> refreshAccessToken() async {
    try {
      final refreshToken = await getRefreshToken();
      final deviceId = await getDeviceId();
      
      if (refreshToken == null) return false;

      final response = await _apiClient.refreshToken({
        'refresh_token': refreshToken,
        'device_id': deviceId,
      });

      await _saveTokens(response);
      return true;
    } catch (e) {
      return false;
    }
  }

  Future<void> logout() async {
    final deviceId = await getDeviceId();
    final refreshToken = await getRefreshToken();
    
    if (refreshToken != null) {
      await _apiClient.logout({
        'device_id': deviceId,
      });
    }
    
    await _clearTokens();
  }

  Future<bool> isAuthenticated() async {
    final token = await getAccessToken();
    return token != null;
  }

  Future<User?> getCurrentUser() async {
    final userJson = _prefs.getString('current_user');
    if (userJson == null) return null;
    
    try {
      return User.fromJson(json.decode(userJson));
    } catch (e) {
      return null;
    }
  }

  // Приватные методы
  Future<void> _saveTokens(Map<String, dynamic> response) async {
    await _prefs.setString('access_token', response['access_token']);
    await _prefs.setString('refresh_token', response['refresh_token']);
    
    if (response['user'] != null) {
      await _prefs.setString('current_user', json.encode(response['user']));
    }
  }

  Future<void> _clearTokens() async {
    await _prefs.remove('access_token');
    await _prefs.remove('refresh_token');
    await _prefs.remove('current_user');
  }
}