import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../presentation/pages/shell/app_shell.dart';
import '../../presentation/pages/auth/login_screen.dart';
import '../../presentation/pages/auth/register_screen.dart';
import '../../presentation/pages/auth/restore_screen.dart';
import '../../presentation/pages/onboarding/onboarding_screen.dart';
import '../../presentation/pages/calendar/calendar_day_screen.dart';
import '../../presentation/pages/calendar/calendar_week_screen.dart';
import '../../presentation/pages/tasks/tasks_screen.dart';
import '../../presentation/pages/inbox/inbox_screen.dart';
import '../../presentation/pages/settings/settings_screen.dart';
import '../../presentation/pages/settings/ai_rules_screen.dart';
import '../../presentation/pages/pro/pro_screen.dart';
import '../../presentation/pages/finance/finance_screen.dart';
import '../../presentation/pages/notifications/notifications_screen.dart';
import '../../presentation/pages/profile/profile_screen.dart';
import '../../presentation/providers/presentation_providers.dart';
import 'routes.dart';

final appRouterProvider = Provider<GoRouter>((ref) {
  final authNotifier = ref.read(authControllerProvider.notifier);
  final authState = ref.watch(authControllerProvider);

  return GoRouter(
    initialLocation: Routes.login,
    refreshListenable: GoRouterRefreshStream(authNotifier.stream),
    redirect: (context, state) {
      final isAuthRoute =
          state.matchedLocation == Routes.login || state.matchedLocation == Routes.register;
      final isAuthenticated = authState.isAuthenticated;

      if (!isAuthenticated && !isAuthRoute) {
        return Routes.login;
      }

      if (isAuthenticated && isAuthRoute) {
        return Routes.tasks;
      }

      return null;
    },
    routes: <RouteBase>[
      GoRoute(
        path: Routes.login,
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: Routes.register,
        builder: (context, state) => const RegisterScreen(),
      ),
      GoRoute(
        path: Routes.restore,
        builder: (context, state) => const RestoreScreen(),
      ),
      GoRoute(
        path: Routes.onboarding,
        builder: (context, state) => const OnboardingScreen(),
      ),
      ShellRoute(
        builder: (context, state, child) => AppShell(child: child),
        routes: <RouteBase>[
          GoRoute(
            path: Routes.calendarDay,
            builder: (context, state) => const CalendarDayScreen(),
          ),
          GoRoute(
            path: Routes.calendarWeek,
            builder: (context, state) => const CalendarWeekScreen(),
          ),
          GoRoute(
            path: Routes.tasks,
            builder: (context, state) => const TasksScreen(),
          ),
          GoRoute(
            path: Routes.inbox,
            builder: (context, state) => const InboxScreen(),
          ),
          GoRoute(
            path: Routes.settings,
            builder: (context, state) => const SettingsScreen(),
          ),
          GoRoute(
            path: Routes.aiRules,
            builder: (context, state) => const AiRulesScreen(),
          ),
          GoRoute(
            path: Routes.pro,
            builder: (context, state) => const ProScreen(),
          ),
          GoRoute(
            path: Routes.finance,
            builder: (context, state) => const FinanceScreen(),
          ),
          GoRoute(
            path: Routes.notifications,
            builder: (context, state) => const NotificationsScreen(),
          ),
          GoRoute(
            path: Routes.profile,
            builder: (context, state) => const ProfileScreen(),
          ),
        ],
      ),
    ],
  );
});
