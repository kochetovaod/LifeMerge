import '../domain/auth_error_code.dart';

class AuthState {
  const AuthState({
    this.isLoading = false,
    this.isAuthenticated = false,
    this.email,
    this.token,
    this.errorMessage,
    this.errorCode,
  });

  final bool isLoading;
  final bool isAuthenticated;
  final String? email;
  final String? token;
  final String? errorMessage;
  final AuthErrorCode? errorCode;

  AuthState copyWith({
    bool? isLoading,
    bool? isAuthenticated,
    String? email,
    String? token,
    String? errorMessage,
    AuthErrorCode? errorCode,
    bool clearError = false,
  }) {
    return AuthState(
      isLoading: isLoading ?? this.isLoading,
      isAuthenticated: isAuthenticated ?? this.isAuthenticated,
      email: email ?? this.email,
      token: token ?? this.token,
      errorMessage: clearError ? null : (errorMessage ?? this.errorMessage),
      errorCode: clearError ? null : (errorCode ?? this.errorCode),
    );
  }
}
