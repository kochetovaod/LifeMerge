import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/l10n/app_localizations.dart';
import '../application/ai_rules_controller.dart';
import '../domain/ai_rules_state.dart';

class AiRulesScreen extends ConsumerWidget {
  const AiRulesScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final state = ref.watch(aiRulesControllerProvider);
    final controller = ref.read(aiRulesControllerProvider.notifier);

    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.aiRulesTitle),
        actions: <Widget>[
          TextButton.icon(
            onPressed: controller.addBreak,
            icon: const Icon(Icons.add),
            label: Text(l10n.addBreak),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            _ProfileScheduleCard(state: state),
            const SizedBox(height: 16),
            _QuietHoursCard(state: state),
            const SizedBox(height: 16),
            _BreaksCard(state: state),
            const SizedBox(height: 16),
            _ForbiddenDaysCard(state: state),
          ],
        ),
      ),
    );
  }
}

class _ProfileScheduleCard extends ConsumerWidget {
  const _ProfileScheduleCard({required this.state});

  final AiRulesState state;

  String _weekdayShort(int weekday, BuildContext context) {
    return <int, String>{
      DateTime.monday: 'Mon',
      DateTime.tuesday: 'Tue',
      DateTime.wednesday: 'Wed',
      DateTime.thursday: 'Thu',
      DateTime.friday: 'Fri',
      DateTime.saturday: 'Sat',
      DateTime.sunday: 'Sun',
    }[weekday]!
        .toUpperCase();
  }

  String _formatTime(BuildContext context, TimeOfDay time) {
    return MaterialLocalizations.of(context).formatTimeOfDay(time,
        alwaysUse24HourFormat: true);
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final workingDays = state.profileSchedule.workingDays.toList()..sort();

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text(l10n.profileScheduleTitle,
                style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            Row(
              children: <Widget>[
                const Icon(Icons.access_time, size: 20),
                const SizedBox(width: 8),
                Text(
                  '${_formatTime(context, state.profileSchedule.workStart)} - ${_formatTime(context, state.profileSchedule.workEnd)}',
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
              ],
            ),
            const SizedBox(height: 8),
            Row(
              children: <Widget>[
                const Icon(Icons.public, size: 20),
                const SizedBox(width: 8),
                Text('${l10n.timezoneLabel} ${state.profileSchedule.timezone}'),
              ],
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              children: workingDays
                  .map((weekday) => Chip(
                        avatar: const Icon(Icons.work_outline, size: 18),
                        label: Text(_weekdayShort(weekday, context)),
                      ))
                  .toList(),
            ),
            const SizedBox(height: 8),
            Text(l10n.profileScheduleHint,
                style: Theme.of(context).textTheme.bodySmall),
          ],
        ),
      ),
    );
  }
}

class _QuietHoursCard extends ConsumerWidget {
  const _QuietHoursCard({required this.state});

  final AiRulesState state;

  Future<void> _pickTime(
    BuildContext context,
    TimeOfDay initialTime,
    void Function(TimeOfDay) onSelected,
  ) async {
    final picked = await showTimePicker(
      context: context,
      initialTime: initialTime,
      builder: (context, child) => MediaQuery(
        data: MediaQuery.of(context).copyWith(alwaysUse24HourFormat: true),
        child: child!,
      ),
    );

    if (picked != null) {
      onSelected(picked);
    }
  }

  String _formatTime(BuildContext context, TimeOfDay time) {
    return MaterialLocalizations.of(context).formatTimeOfDay(
      time,
      alwaysUse24HourFormat: true,
    );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final controller = ref.read(aiRulesControllerProvider.notifier);

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: <Widget>[
                Text(l10n.quietHoursTitle,
                    style: Theme.of(context).textTheme.titleMedium),
                Switch(
                  value: state.quietHoursEnabled,
                  onChanged: controller.toggleQuietHours,
                ),
              ],
            ),
            const SizedBox(height: 4),
            Text(l10n.quietHoursDescription),
            const SizedBox(height: 12),
            Row(
              children: <Widget>[
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: state.quietHoursEnabled
                        ? () => _pickTime(
                              context,
                              state.quietHoursStart,
                              controller.updateQuietStart,
                            )
                        : null,
                    icon: const Icon(Icons.nightlight_round),
                    label: Text('${l10n.startLabel} ${_formatTime(context, state.quietHoursStart)}'),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: state.quietHoursEnabled
                        ? () => _pickTime(
                              context,
                              state.quietHoursEnd,
                              controller.updateQuietEnd,
                            )
                        : null,
                    icon: const Icon(Icons.sunny),
                    label: Text('${l10n.endLabel} ${_formatTime(context, state.quietHoursEnd)}'),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _BreaksCard extends ConsumerWidget {
  const _BreaksCard({required this.state});

  final AiRulesState state;

  String _formatTime(BuildContext context, TimeOfDay time) {
    return MaterialLocalizations.of(context).formatTimeOfDay(time,
        alwaysUse24HourFormat: true);
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final controller = ref.read(aiRulesControllerProvider.notifier);

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text(l10n.breaksTitle, style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 4),
            Text(l10n.breaksDescription),
            const SizedBox(height: 12),
            ...state.breaks.asMap().entries.map((entry) {
              final index = entry.key;
              final restBreak = entry.value;
              return Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: <Widget>[
                        Text(restBreak.label,
                            style: Theme.of(context).textTheme.titleSmall),
                        Text('${restBreak.duration.inMinutes} min'),
                      ],
                    ),
                    const SizedBox(height: 4),
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: <Widget>[
                        ActionChip(
                          avatar: const Icon(Icons.play_circle_outline),
                          label: Text('${l10n.startLabel} ${_formatTime(context, restBreak.start)}'),
                          onPressed: () async {
                            final picked = await showTimePicker(
                              context: context,
                              initialTime: restBreak.start,
                              builder: (context, child) => MediaQuery(
                                data: MediaQuery.of(context)
                                    .copyWith(alwaysUse24HourFormat: true),
                                child: child!,
                              ),
                            );
                            if (picked != null) {
                              controller.updateBreakStart(index, picked);
                            }
                          },
                        ),
                        InputChip(
                          avatar: const Icon(Icons.timer_outlined),
                          label: Text(l10n.durationLabel(restBreak.duration)),
                          onPressed: () async {
                            final minutes = await showModalBottomSheet<int>(
                              context: context,
                              builder: (context) {
                                return _DurationPicker(
                                  initialMinutes: restBreak.duration.inMinutes,
                                  label: restBreak.label,
                                );
                              },
                            );
                            if (minutes != null) {
                              controller.updateBreakDuration(
                                index,
                                Duration(minutes: minutes),
                              );
                            }
                          },
                        ),
                      ],
                    ),
                  ],
                ),
              );
            }),
          ],
        ),
      ),
    );
  }
}

class _ForbiddenDaysCard extends ConsumerWidget {
  const _ForbiddenDaysCard({required this.state});

  final AiRulesState state;

  String _weekdayLabel(int weekday, BuildContext context) {
    const labels = <int, String>{
      DateTime.monday: 'Mon',
      DateTime.tuesday: 'Tue',
      DateTime.wednesday: 'Wed',
      DateTime.thursday: 'Thu',
      DateTime.friday: 'Fri',
      DateTime.saturday: 'Sat',
      DateTime.sunday: 'Sun',
    };
    return labels[weekday]!;
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final controller = ref.read(aiRulesControllerProvider.notifier);
    final l10n = AppLocalizations.of(context);

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text(l10n.forbiddenDaysTitle,
                style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 4),
            Text(l10n.forbiddenDaysDescription),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: List<Widget>.generate(7, (index) {
                final weekday = index + 1;
                final isBlocked = state.forbiddenWeekdays.contains(weekday);
                final isWorkingDay = state.profileSchedule.isWorkingDay(weekday);

                return FilterChip(
                  avatar: Icon(
                    isBlocked ? Icons.block : Icons.check_circle_outline,
                    size: 18,
                  ),
                  selected: isBlocked,
                  onSelected: (_) => controller.toggleForbiddenWeekday(weekday),
                  label: Text(_weekdayLabel(weekday, context)),
                  tooltip: isWorkingDay
                      ? l10n.forbiddenWorkdayTooltip
                      : l10n.forbiddenDayTooltip,
                );
              }),
            ),
          ],
        ),
      ),
    );
  }
}

class _DurationPicker extends StatefulWidget {
  const _DurationPicker({required this.initialMinutes, required this.label});

  final int initialMinutes;
  final String label;

  @override
  State<_DurationPicker> createState() => _DurationPickerState();
}

class _DurationPickerState extends State<_DurationPicker> {
  late double _minutes;

  @override
  void initState() {
    super.initState();
    _minutes = widget.initialMinutes.toDouble();
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 24, 16, 32),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text(widget.label, style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 12),
          Row(
            children: <Widget>[
              const Icon(Icons.timer_outlined),
              const SizedBox(width: 8),
              Text('${_minutes.round()} min'),
            ],
          ),
          Slider(
            value: _minutes,
            min: 5,
            max: 90,
            divisions: 17,
            label: '${_minutes.round()} min',
            onChanged: (value) => setState(() => _minutes = value),
          ),
          const SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.end,
            children: <Widget>[
              TextButton(
                onPressed: () => Navigator.of(context).pop(),
                child: const Text('Cancel'),
              ),
              const SizedBox(width: 8),
              ElevatedButton(
                onPressed: () =>
                    Navigator.of(context).pop<int>(_minutes.round()),
                child: const Text('Save'),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
