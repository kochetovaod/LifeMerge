import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../core/routing/routes.dart';

class AppShell extends StatelessWidget {
  const AppShell({required this.child, super.key});

  final Widget child;

  int _indexForLocation(String location) {
    if (location.startsWith(Routes.calendarDay) || location.startsWith(Routes.calendarWeek)) return 0;
    if (location.startsWith(Routes.tasks)) return 1;
    if (location.startsWith(Routes.inbox)) return 2;
    if (location.startsWith(Routes.settings)) return 3;
    if (location.startsWith(Routes.pro)) return 4;
    return 0;
  }

  void _onTap(BuildContext context, int index) {
    switch (index) {
      case 0:
        context.go(Routes.calendarDay);
      case 1:
        context.go(Routes.tasks);
      case 2:
        context.go(Routes.inbox);
      case 3:
        context.go(Routes.settings);
      case 4:
        context.go(Routes.pro);
    }
  }

  @override
  Widget build(BuildContext context) {
    final location = GoRouterState.of(context).uri.toString();
    final currentIndex = _indexForLocation(location);

    return Scaffold(
      body: SafeArea(child: child),
      bottomNavigationBar: NavigationBar(
        selectedIndex: currentIndex,
        onDestinationSelected: (i) => _onTap(context, i),
        destinations: const <NavigationDestination>[
          NavigationDestination(icon: Icon(Icons.calendar_today), label: 'Calendar'),
          NavigationDestination(icon: Icon(Icons.check_circle_outline), label: 'Tasks'),
          NavigationDestination(icon: Icon(Icons.inbox_outlined), label: 'Inbox'),
          NavigationDestination(icon: Icon(Icons.settings_outlined), label: 'Settings'),
          NavigationDestination(icon: Icon(Icons.workspace_premium_outlined), label: 'Pro'),
        ],
      ),
    );
  }
}
