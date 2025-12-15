import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/analytics/analytics_service.dart';
import '../data/auth_api_service.dart';
import '../data/auth_repository.dart';
import '../domain/auth_error_code.dart';
import 'auth_state.dart';

class AuthController extends StateNotifier<AuthState> {
  AuthController(this._analytics, this._repository) : super(const AuthState());

  final AnalyticsService _analytics;
  final AuthRepository _repository;

  Future<bool> signIn({required String email, required String password}) async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final session = await _repository.login(email: email, password: password);
      state = state.copyWith(
        isLoading: false,
        errorMessage: null,
        isAuthenticated: true,
        email: session.email,
        token: session.token,
        errorCode: null,
      );
      return true;
    } on AuthApiException catch (error) {
      state = state.copyWith(
        isLoading: false,
        isAuthenticated: false,
        errorMessage: error.toString(),
        errorCode: error.code,
      );
      return false;
    } catch (error) {
      state = state.copyWith(
        isLoading: false,
        isAuthenticated: false,
        errorMessage: error.toString(),
        errorCode: AuthErrorCode.unknown,
      );
      return false;
    }
  }

  Future<bool> signUp({required String email, required String password}) async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final session = await _repository.signUp(email: email, password: password);
      await _analytics.logEvent('User_SignUp', parameters: <String, dynamic>{'email': email});
      state = state.copyWith(
        isLoading: false,
        errorMessage: null,
        isAuthenticated: true,
        email: session.email,
        token: session.token,
        errorCode: null,
      );
      return true;
    } on AuthApiException catch (error) {
      state = state.copyWith(
        isLoading: false,
        isAuthenticated: false,
        errorMessage: error.toString(),
        errorCode: error.code,
      );
      return false;
    } catch (error) {
      state = state.copyWith(
        isLoading: false,
        isAuthenticated: false,
        errorMessage: error.toString(),
        errorCode: AuthErrorCode.unknown,
      );
      return false;
    }
  }

  Future<bool> requestPasswordReset(String email) async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      await _repository.requestPasswordReset(email);
      state = state.copyWith(isLoading: false, clearError: true);
      return true;
    } on AuthApiException catch (error) {
      state = state.copyWith(
        isLoading: false,
        errorMessage: error.toString(),
        errorCode: error.code,
      );
      return false;
    } catch (error) {
      state = state.copyWith(
        isLoading: false,
        errorMessage: error.toString(),
        errorCode: AuthErrorCode.unknown,
      );
      return false;
    }
  }

  Future<void> signOut() async {
    final token = state.token;
    state = state.copyWith(isLoading: true, clearError: true);
    if (token != null) {
      await _repository.logout(token);
    }
    state = const AuthState();
  }

  Future<void> restoreSession() async {
    final session = await _repository.restore();
    if (session != null) {
      state = state.copyWith(
        isAuthenticated: true,
        email: session.email,
        token: session.token,
        clearError: true,
      );
    }
  }

  void clearError() {
    if (state.errorMessage != null) {
      state = state.copyWith(clearError: true);
    }
  }
}

final authControllerProvider = StateNotifierProvider<AuthController, AuthState>((ref) {
  final analytics = ref.read(analyticsProvider);
  final repository = ref.read(authRepositoryProvider);
  return AuthController(analytics, repository);
});
