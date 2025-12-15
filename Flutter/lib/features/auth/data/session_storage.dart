import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'auth_repository.dart';

class SessionStorage {
  SessionStorage(this._prefs);

  final SharedPreferences _prefs;

  static const String _keyEmail = 'auth_email';
  static const String _keyToken = 'auth_token';

  Future<void> saveSession(AuthSession session) async {
    await _prefs.setString(_keyEmail, session.email);
    await _prefs.setString(_keyToken, session.token);
  }

  Future<AuthSession?> readSession() async {
    final email = _prefs.getString(_keyEmail);
    final token = _prefs.getString(_keyToken);
    if (email == null || token == null) {
      return null;
    }
    return AuthSession(email: email, token: token);
  }

  Future<void> clear() async {
    await _prefs.remove(_keyEmail);
    await _prefs.remove(_keyToken);
  }
}

final sessionStorageProvider = Provider<SessionStorage>((ref) {
  throw UnimplementedError('SessionStorage must be overridden during bootstrap');
});
