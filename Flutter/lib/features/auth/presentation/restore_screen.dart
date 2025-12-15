import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/routing/routes.dart';
import '../../../core/theme/app_typography.dart';
import '../application/auth_controller.dart';
import '../application/auth_state.dart';
import '../domain/auth_error_code.dart';
import 'widgets/auth_text_field.dart';
import 'widgets/primary_button.dart';

class RestoreScreen extends ConsumerStatefulWidget {
  const RestoreScreen({super.key});

  @override
  ConsumerState<RestoreScreen> createState() => _RestoreScreenState();
}

class _RestoreScreenState extends ConsumerState<RestoreScreen> {
  late final TextEditingController _emailController;
  final GlobalKey<FormState> _formKey = GlobalKey<FormState>();

  @override
  void initState() {
    super.initState();
    _emailController = TextEditingController();
  }

  @override
  void dispose() {
    _emailController.dispose();
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

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final AuthState state = ref.watch(authControllerProvider);
    final authController = ref.read(authControllerProvider.notifier);

    return Scaffold(
      appBar: AppBar(title: const Text('Восстановление доступа')),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 480),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: <Widget>[
                  Text(l10n.resetPasswordTitle, style: AppTypography.h2),
                  const SizedBox(height: 8),
                  Text(
                    'Введите почту, отправим ссылку на восстановление. После смены пароля вас автоматически залогиним.',
                    style: AppTypography.body.copyWith(
                      color: theme.colorScheme.onSurface.withOpacity(0.75),
                    ),
                  ),
                  const SizedBox(height: 24),
                  Form(
                    key: _formKey,
                    child: AuthTextField(
                      label: l10n.emailLabel,
                      controller: _emailController,
                      keyboardType: TextInputType.emailAddress,
                      validator: (value) => _validateEmail(value, l10n),
                      onChanged: (_) {
                        if (state.errorMessage != null) {
                          authController.clearError();
                        }
                      },
                    ),
                  ),
                  const SizedBox(height: 12),
                  if (state.errorMessage != null || state.errorCode != null)
                    Container(
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
                              style: AppTypography.body.copyWith(color: theme.colorScheme.error),
                            ),
                          ),
                        ],
                      ),
                    ),
                  const SizedBox(height: 16),
                  PrimaryButton(
                    label: 'Отправить ссылку',
                    isLoading: state.isLoading,
                    onPressed: () async {
                      if (!_formKey.currentState!.validate()) {
                        return;
                      }
                      final sent = await authController.requestPasswordReset(_emailController.text.trim());
                      if (!mounted) return;
                      final updated = ref.read(authControllerProvider);
                      final message = sent ? l10n.resetPasswordSent : _resolveError(updated, l10n);
                      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
                      if (sent) {
                        await Future<void>.delayed(const Duration(milliseconds: 400));
                        context.go(Routes.login);
                      }
                    },
                  ),
                  TextButton(
                    onPressed: () => context.go(Routes.login),
                    child: const Text('Вернуться к входу'),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
