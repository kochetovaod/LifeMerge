import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/routing/routes.dart';
import '../../auth/application/auth_controller.dart';

class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final authState = ref.watch(authControllerProvider);
    final authController = ref.read(authControllerProvider.notifier);

    return Scaffold(
      appBar: AppBar(title: Text(l10n.logout)),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            Card(
              child: ListTile(
                leading: const Icon(Icons.person_outline),
                title: Text(authState.email ?? 'Guest'),
                subtitle: Text(l10n.logoutDescription),
              ),
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: authState.isLoading
                  ? null
                  : () async {
                      await authController.signOut();
                      if (!context.mounted) return;
                      context.go(Routes.login);
                    },
              icon: const Icon(Icons.logout),
              label: Text(l10n.logout),
            ),
          ],
        ),
      ),
    );
  }
}
