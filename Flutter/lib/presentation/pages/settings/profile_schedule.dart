import 'package:flutter/material.dart';

class ProfileSchedule {
  const ProfileSchedule({
    required this.timezone,
    required this.workStart,
    required this.workEnd,
    required this.workingDays,
  });

  final String timezone;
  final TimeOfDay workStart;
  final TimeOfDay workEnd;
  final Set<int> workingDays;

  bool isWorkingDay(int weekday) => workingDays.contains(weekday);
}
