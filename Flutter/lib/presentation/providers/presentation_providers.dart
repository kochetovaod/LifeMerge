import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../app/di/providers.dart';
import '../blocs/auth/auth_controller.dart';
import '../blocs/auth/auth_state.dart';
import '../blocs/calendar/calendar_controller.dart';
import '../blocs/calendar/calendar_state.dart';
import '../blocs/inbox/inbox_controller.dart';
import '../blocs/inbox/inbox_state.dart';
import '../blocs/settings/ai_rules_controller.dart';
import '../blocs/settings/ai_rules_state.dart';
import '../blocs/tasks/tasks_controller.dart';
import '../blocs/tasks/tasks_state.dart';
import '../pages/settings/profile_schedule.dart';

final authControllerProvider = StateNotifierProvider<AuthController, AuthState>((ref) {
  return AuthController(ref.read(authRepositoryProvider));
});

final calendarControllerProvider =
    StateNotifierProvider<CalendarController, CalendarState>((ref) {
  return CalendarController(ref.read(calendarRepositoryProvider));
});

final tasksControllerProvider = StateNotifierProvider<TasksController, TasksState>((ref) {
  return TasksController(ref.read(tasksRepositoryProvider));
});

final inboxControllerProvider = StateNotifierProvider<InboxController, InboxState>((ref) {
  return InboxController(ref.read(inboxRepositoryProvider));
});

final profileScheduleProvider = Provider<ProfileSchedule>((ref) {
  return ProfileSchedule(
    timezone: 'Europe/Moscow',
    workStart: const TimeOfDay(hour: 9, minute: 0),
    workEnd: const TimeOfDay(hour: 18, minute: 0),
    workingDays: const <int>{
      DateTime.monday,
      DateTime.tuesday,
      DateTime.wednesday,
      DateTime.thursday,
      DateTime.friday,
    },
  );
});

final aiRulesControllerProvider = StateNotifierProvider<AiRulesController, AiRulesState>((ref) {
  final schedule = ref.watch(profileScheduleProvider);
  return AiRulesController(schedule);
});
