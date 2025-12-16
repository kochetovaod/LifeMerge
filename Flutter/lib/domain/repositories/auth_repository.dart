import '../entities/auth/user.dart';

abstract class AuthRepository {
  Future<String?> getAccessToken();
  Future<String?> getRefreshToken();
  Future<String> getDeviceId();

  Future<User> signup({
    required String email,
    required String password,
    required String fullName,
    String timezone,
  });

  Future<User> login({
    required String email,
    required String password,
  });

  Future<bool> refreshAccessToken();
  Future<void> logout();
  Future<bool> isAuthenticated();
  Future<User?> getCurrentUser();
}
