import 'package:flutter/material.dart';

import 'profile_schedule.dart';

class RestBreak {
  const RestBreak({
    required this.label,
    required this.start,
    required this.duration,
  });

  final String label;
  final TimeOfDay start;
  final Duration duration;

  RestBreak copyWith({String? label, TimeOfDay? start, Duration? duration}) {
    return RestBreak(
      label: label ?? this.label,
      start: start ?? this.start,
      duration: duration ?? this.duration,
    );
  }
}

class AiRulesState {
  const AiRulesState({
    required this.profileSchedule,
    required this.quietHoursEnabled,
    required this.quietHoursStart,
    required this.quietHoursEnd,
    required this.breaks,
    required this.forbiddenWeekdays,
  });

  factory AiRulesState.initial(ProfileSchedule profileSchedule) {
    return AiRulesState(
      profileSchedule: profileSchedule,
      quietHoursEnabled: true,
      quietHoursStart: const TimeOfDay(hour: 22, minute: 0),
      quietHoursEnd: const TimeOfDay(hour: 7, minute: 0),
      breaks: const <RestBreak>[
        RestBreak(label: 'Lunch', start: TimeOfDay(hour: 13, minute: 0), duration: Duration(minutes: 45)),
        RestBreak(label: 'Walk', start: TimeOfDay(hour: 16, minute: 0), duration: Duration(minutes: 15)),
      ],
      forbiddenWeekdays: const <int>{DateTime.saturday, DateTime.sunday},
    );
  }

  final ProfileSchedule profileSchedule;
  final bool quietHoursEnabled;
  final TimeOfDay quietHoursStart;
  final TimeOfDay quietHoursEnd;
  final List<RestBreak> breaks;
  final Set<int> forbiddenWeekdays;

  AiRulesState copyWith({
    ProfileSchedule? profileSchedule,
    bool? quietHoursEnabled,
    TimeOfDay? quietHoursStart,
    TimeOfDay? quietHoursEnd,
    List<RestBreak>? breaks,
    Set<int>? forbiddenWeekdays,
  }) {
    return AiRulesState(
      profileSchedule: profileSchedule ?? this.profileSchedule,
      quietHoursEnabled: quietHoursEnabled ?? this.quietHoursEnabled,
      quietHoursStart: quietHoursStart ?? this.quietHoursStart,
      quietHoursEnd: quietHoursEnd ?? this.quietHoursEnd,
      breaks: breaks ?? this.breaks,
      forbiddenWeekdays: forbiddenWeekdays ?? this.forbiddenWeekdays,
    );
  }
}
