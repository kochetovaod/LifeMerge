import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../domain/repositories/auth_repository.dart';
import 'auth_state.dart';

class AuthController extends StateNotifier<AuthState> {
  AuthController(this._repo) : super(const AuthInitial());

  final AuthRepository _repo;

  void clearError() {
    if (state is AuthError) {
      state = const AuthUnauthenticated();
    }
  }

  Future<bool> requestPasswordReset(String email) async {
    // Stubbed flow until backend support is added.
    clearError();
    return email.isNotEmpty;
  }

  Future<void> restoreSession() async {
    final isAuthed = await _repo.isAuthenticated();
    if (!isAuthed) {
      state = const AuthUnauthenticated();
      return;
    }
    final user = await _repo.getCurrentUser();
    if (user == null) {
      state = const AuthUnauthenticated();
      return;
    }
    state = AuthAuthenticated(user: user);
  }

  Future<bool> signIn({required String email, required String password}) async {
    state = const AuthLoading();
    try {
      final user = await _repo.login(email: email, password: password);
      state = AuthAuthenticated(user: user);
      return true;
    } catch (e) {
      state = AuthError(e.toString());
      return false;
    }
  }

  Future<bool> signUp({
    required String email,
    required String password,
    required String fullName,
    String timezone = 'UTC',
  }) async {
    state = const AuthLoading();
    try {
      final user = await _repo.signup(
        email: email,
        password: password,
        fullName: fullName,
        timezone: timezone,
      );
      state = AuthAuthenticated(user: user);
      return true;
    } catch (e) {
      state = AuthError(e.toString());
      return false;
    }
  }

  Future<void> signOut() async {
    state = const AuthLoading();
    try {
      await _repo.logout();
    } finally {
      state = const AuthUnauthenticated();
    }
  }
}
