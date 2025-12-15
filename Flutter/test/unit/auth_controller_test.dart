import 'package:flutter_test/flutter_test.dart';

import 'package:lifemerge/core/analytics/analytics_service.dart';
import 'package:lifemerge/features/auth/application/auth_controller.dart';
import 'package:lifemerge/features/auth/application/auth_state.dart';
import 'package:lifemerge/features/auth/data/auth_repository.dart';
import 'package:lifemerge/features/auth/data/auth_api_service.dart';
import 'package:lifemerge/features/auth/domain/auth_error_code.dart';

class FakeAnalyticsService extends AnalyticsService {
  FakeAnalyticsService();

  String? lastEvent;
  Map<String, dynamic>? lastParameters;

  @override
  Future<void> logEvent(String name, {Map<String, dynamic>? parameters}) async {
    lastEvent = name;
    lastParameters = parameters;
  }
}

class FakeAuthRepository implements AuthRepository {
  FakeAuthRepository();

  AuthSession? storedSession;
  AuthApiException? loginError;
  AuthApiException? signupError;
  AuthApiException? resetError;
  bool logoutCalled = false;

  @override
  Future<AuthSession> login({required String email, required String password}) async {
    if (loginError != null) throw loginError!;
    final session = AuthSession(email: email, token: 'token-$email');
    storedSession = session;
    return session;
  }

  @override
  Future<AuthSession> signUp({required String email, required String password}) async {
    if (signupError != null) throw signupError!;
    final session = AuthSession(email: email, token: 'signup-$email');
    storedSession = session;
    return session;
  }

  @override
  Future<void> requestPasswordReset(String email) async {
    if (resetError != null) throw resetError!;
  }

  @override
  Future<void> logout(String token) async {
    logoutCalled = true;
    storedSession = null;
  }

  @override
  Future<AuthSession?> restore() async => storedSession;
}

void main() {
  group('AuthController', () {
    late FakeAnalyticsService analytics;
    late FakeAuthRepository repository;
    late AuthController controller;

    setUp(() {
      analytics = FakeAnalyticsService();
      repository = FakeAuthRepository();
      controller = AuthController(analytics, repository);
    });

    test('signIn sets authenticated state on success', () async {
      final success = await controller.signIn(email: 'demo@lifemerge.app', password: 'demo1234');

      expect(success, isTrue);
      expect(controller.state.isAuthenticated, isTrue);
      expect(controller.state.email, 'demo@lifemerge.app');
      expect(controller.state.errorMessage, isNull);
    });

    test('signIn captures API errors', () async {
      repository.loginError = AuthApiException(AuthErrorCode.incorrectCredentials, 'Bad creds');

      final success = await controller.signIn(email: 'user@test.com', password: 'wrong');

      expect(success, isFalse);
      expect(controller.state.isAuthenticated, isFalse);
      expect(controller.state.errorCode, AuthErrorCode.incorrectCredentials);
      expect(controller.state.errorMessage, 'Bad creds');
    });

    test('signUp logs analytics event and stores session', () async {
      final success = await controller.signUp(email: 'new@lifemerge.app', password: 'demo1234');

      expect(success, isTrue);
      expect(controller.state.token, isNotNull);
      expect(analytics.lastEvent, 'User_SignUp');
      expect(analytics.lastParameters, containsPair('email', 'new@lifemerge.app'));
    });

    test('signOut clears state and calls repository', () async {
      repository.storedSession = const AuthSession(email: 'demo@lifemerge.app', token: 'token');
      controller = AuthController(analytics, repository);
      controller.state = const AuthState(isAuthenticated: true, email: 'demo@lifemerge.app', token: 'token');

      await controller.signOut();

      expect(controller.state.isAuthenticated, isFalse);
      expect(controller.state.token, isNull);
      expect(repository.logoutCalled, isTrue);
    });
  });
}
