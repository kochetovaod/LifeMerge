import 'dart:async';

class AuthApiService {
  final Map<String, String> _users = <String, String>{
    'demo@lifemerge.app': 'demo1234',
  };

  Future<String> signUp({required String email, required String password}) async {
    await Future<void>.delayed(const Duration(milliseconds: 650));
    if (_users.containsKey(email)) {
      throw AuthApiException(
        AuthErrorCode.accountExists,
        'Account already exists for this email',
      );
    }
    _users[email] = password;
    return _issueToken(email);
  }

  Future<String> login({required String email, required String password}) async {
    await Future<void>.delayed(const Duration(milliseconds: 450));
    final stored = _users[email];
    if (stored == null || stored != password) {
      throw AuthApiException(
        AuthErrorCode.incorrectCredentials,
        'Incorrect email or password',
      );
    }
    return _issueToken(email);
  }

  Future<void> requestPasswordReset(String email) async {
    await Future<void>.delayed(const Duration(milliseconds: 500));
    if (!_users.containsKey(email)) {
      throw AuthApiException(
        AuthErrorCode.userNotFound,
        'No account found for $email',
      );
    }
  }

  Future<void> logout(String token) async {
    await Future<void>.delayed(const Duration(milliseconds: 200));
  }

  String _issueToken(String email) => 'token-${email.hashCode}-${DateTime.now().millisecondsSinceEpoch}';
}

class AuthApiException implements Exception {
  AuthApiException(this.code, this.message);

  final AuthErrorCode code;
  final String message;

  @override
  String toString() => message;
}
import '../domain/auth_error_code.dart';
