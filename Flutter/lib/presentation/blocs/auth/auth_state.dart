import '../../../domain/entities/auth/user.dart';
import '../../../domain/value_objects/auth/auth_error_code.dart';

sealed class AuthState {
  const AuthState();

  bool get isLoading => this is AuthLoading;
  bool get isAuthenticated => this is AuthAuthenticated;

  String? get errorMessage => (this is AuthError) ? (this as AuthError).message : null;
  AuthErrorCode? get errorCode => (this is AuthError) ? (this as AuthError).code : null;
}

class AuthInitial extends AuthState {
  const AuthInitial();
}

class AuthLoading extends AuthState {
  const AuthLoading();
}

class AuthAuthenticated extends AuthState {
  const AuthAuthenticated({required this.user});
  final User user;
}

class AuthUnauthenticated extends AuthState {
  const AuthUnauthenticated();
}

class AuthError extends AuthState {
  const AuthError(this.message, {this.code});
  final String message;
  final AuthErrorCode? code;
}
