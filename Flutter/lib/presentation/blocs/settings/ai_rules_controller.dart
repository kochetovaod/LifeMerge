import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../pages/settings/profile_schedule.dart';
import 'ai_rules_state.dart';

class AiRulesController extends StateNotifier<AiRulesState> {
  AiRulesController(ProfileSchedule profileSchedule)
      : super(AiRulesState.initial(profileSchedule));

  void toggleQuietHours(bool isEnabled) {
    state = state.copyWith(quietHoursEnabled: isEnabled);
  }

  void updateQuietStart(TimeOfDay start) {
    state = state.copyWith(quietHoursStart: start);
  }

  void updateQuietEnd(TimeOfDay end) {
    state = state.copyWith(quietHoursEnd: end);
  }

  void toggleForbiddenWeekday(int weekday) {
    final updated = <int>{...state.forbiddenWeekdays};
    if (!updated.add(weekday)) {
      updated.remove(weekday);
    }
    state = state.copyWith(forbiddenWeekdays: updated);
  }

  void updateBreakStart(int index, TimeOfDay start) {
    final breaks = List<RestBreak>.from(state.breaks);
    if (index >= breaks.length) return;

    final adjusted = _clampToWorkday(start);
    breaks[index] = breaks[index].copyWith(start: adjusted);
    state = state.copyWith(breaks: breaks);
  }

  void updateBreakDuration(int index, Duration duration) {
    final breaks = List<RestBreak>.from(state.breaks);
    if (index >= breaks.length) return;

    breaks[index] = breaks[index].copyWith(duration: duration);
    state = state.copyWith(breaks: breaks);
  }

  void addBreak() {
    final defaultStart = state.profileSchedule.workStart.replacing(
      hour: 13,
      minute: 0,
    );

    state = state.copyWith(
      breaks: <RestBreak>[
        ...state.breaks,
        RestBreak(
          label: 'Custom break',
          start: defaultStart,
          duration: const Duration(minutes: 20),
        ),
      ],
    );
  }

  TimeOfDay _clampToWorkday(TimeOfDay time) {
    final start = state.profileSchedule.workStart;
    final end = state.profileSchedule.workEnd;

    if (_minutes(time) < _minutes(start)) return start;
    if (_minutes(time) > _minutes(end)) return end;
    return time;
  }

  int _minutes(TimeOfDay time) => time.hour * 60 + time.minute;
}
