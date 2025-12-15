import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/routing/routes.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_typography.dart';
import '../application/auth_controller.dart';
import '../application/auth_state.dart';
import '../domain/auth_error_code.dart';
import 'widgets/auth_text_field.dart';
import 'widgets/primary_button.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  late final TextEditingController _emailController;
  late final TextEditingController _passwordController;
  final GlobalKey<FormState> _formKey = GlobalKey<FormState>();

  @override
  void initState() {
    super.initState();
    _emailController = TextEditingController();
    _passwordController = TextEditingController();
  }

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  String? _validateEmail(String? value, AppLocalizations l10n) {
    if (value == null || value.isEmpty) {
      return l10n.fieldRequired;
    }
    final isValid = RegExp(r'^[^@]+@[^@]+\.[^@]+$').hasMatch(value.trim());
    if (!isValid) {
      return l10n.invalidEmail;
    }
    return null;
  }

  String _resolveError(AuthState state, AppLocalizations l10n) {
    switch (state.errorCode) {
      case AuthErrorCode.incorrectCredentials:
        return l10n.incorrectCredentials;
      case AuthErrorCode.accountExists:
        return l10n.accountExists;
      case AuthErrorCode.userNotFound:
        return l10n.userNotFound;
      case AuthErrorCode.unknown:
      case null:
        return state.errorMessage ?? l10n.genericError;
    }
  }

  String? _validatePassword(String? value, AppLocalizations l10n) {
    if (value == null || value.isEmpty) {
      return l10n.fieldRequired;
    }
    if (value.length < 8) {
      return l10n.passwordTooShort;
    }
    return null;
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final isLight = theme.brightness == Brightness.light;
    final AuthState state = ref.watch(authControllerProvider);
    final authController = ref.read(authControllerProvider.notifier);

    void clearError(String value) {
      if (state.errorMessage != null) {
        authController.clearError();
      }
    }

    Future<void> handlePasswordReset() async {
      final emailError = _validateEmail(_emailController.text.trim(), l10n);
      if (emailError != null) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(emailError)),
        );
        return;
      }

      final success = await authController.requestPasswordReset(_emailController.text.trim());
      if (!mounted) return;
      final updatedState = ref.read(authControllerProvider);
      final message = success ? l10n.resetPasswordSent : _resolveError(updatedState, l10n);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(message)),
      );
    }

    return Scaffold(
      body: SafeArea(
        child: Container(
          decoration: BoxDecoration(
            color: theme.scaffoldBackgroundColor,
            gradient: isLight
                ? const LinearGradient(
                    colors: <Color>[Color(0xFFF7F9FC), Color(0xFFE7ECF6)],
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                  )
                : null,
          ),
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 480),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: <Widget>[
                    Align(
                      alignment: Alignment.centerLeft,
                      child: Text(
                        l10n.appName,
                        style: AppTypography.h1.copyWith(color: AppColors.primary),
                      ),
                    ),
                    const SizedBox(height: 32),
                    Text(
                      l10n.loginTitle,
                      style: AppTypography.h2.copyWith(color: theme.colorScheme.onSurface),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      l10n.loginSubtitle,
                      style: AppTypography.body.copyWith(color: theme.colorScheme.onSurface.withOpacity(0.7)),
                    ),
                    const SizedBox(height: 32),
                    Form(
                      key: _formKey,
                      child: Column(
                        children: <Widget>[
                          AuthTextField(
                            label: l10n.emailLabel,
                            controller: _emailController,
                            keyboardType: TextInputType.emailAddress,
                            validator: (value) => _validateEmail(value, l10n),
                            onChanged: clearError,
                          ),
                          const SizedBox(height: 16),
                          AuthTextField(
                            label: l10n.passwordLabel,
                            controller: _passwordController,
                            obscureText: true,
                            validator: (value) => _validatePassword(value, l10n),
                            onChanged: clearError,
                          ),
                          const SizedBox(height: 12),
                          Align(
                            alignment: Alignment.centerRight,
                            child: TextButton(
                              onPressed: state.isLoading ? null : () => context.go(Routes.restore),
                              child: Text(l10n.forgotPassword),
                            ),
                          ),
                          const SizedBox(height: 12),
                          PrimaryButton(
                            label: l10n.continueButton,
                            isLoading: state.isLoading,
                            onPressed: () async {
                              if (!_formKey.currentState!.validate()) {
                                return;
                              }
                              final success = await authController.signIn(
                                email: _emailController.text.trim(),
                                password: _passwordController.text,
                              );
                              if (!mounted) return;
                              if (success) {
                                context.go(Routes.onboarding);
                              } else {
                                final updatedState =
                                    ref.read(authControllerProvider);
                                if (updatedState.errorMessage != null || updatedState.errorCode != null) {
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    SnackBar(
                                      content: Text(_resolveError(updatedState, l10n)),
                                    ),
                                  );
                                }
                              }
                            },
                          ),
                          if (state.errorMessage != null || state.errorCode != null) ...<Widget>[
                            const SizedBox(height: 12),
                            Container(
                              width: double.infinity,
                              padding: const EdgeInsets.all(12),
                              decoration: BoxDecoration(
                                color: theme.colorScheme.error.withOpacity(0.08),
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: Row(
                                children: <Widget>[
                                  Icon(Icons.error_outline, color: theme.colorScheme.error),
                                  const SizedBox(width: 8),
                                  Expanded(
                                    child: Text(
                                      _resolveError(state, l10n),
                                      style: AppTypography.body.copyWith(
                                        color: theme.colorScheme.error,
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ],
                      ),
                    ),
                    const SizedBox(height: 24),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: <Widget>[
                        Text(
                          l10n.noAccountYet,
                          style: AppTypography.body.copyWith(
                            color: theme.colorScheme.onSurface.withOpacity(0.8),
                          ),
                        ),
                        TextButton(
                          onPressed: state.isLoading ? null : () => context.go(Routes.register),
                          child: Text(l10n.createAccount),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
