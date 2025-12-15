import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../calendar/application/calendar_controller.dart';
import '../../calendar/domain/calendar_event.dart';

class ProScreen extends ConsumerStatefulWidget {
  const ProScreen({super.key});

  @override
  ConsumerState<ProScreen> createState() => _ProScreenState();
}

class _ProScreenState extends State<ProScreen> {
  late final DateTime _trialEndsAt;
  late Duration _timeLeft;
  Timer? _ticker;
  bool _isPlanning = false;
  bool _isUpgrading = false;

  bool get _isTrialActive => _timeLeft > Duration.zero;
class _ProScreenState extends ConsumerState<ProScreen> {
  bool _isPlanning = false;
  bool _trialRequested = false;
  bool _isApplying = false;

  late List<_AiPlanEntry> _planEntries;

  @override
  void initState() {
    super.initState();
    // TODO: заменить на реальную дату окончания триала из профиля пользователя
    _trialEndsAt = DateTime.now().add(const Duration(days: 9, hours: 4, minutes: 36));
    _timeLeft = _remainingTime();
    _ticker = Timer.periodic(const Duration(seconds: 1), (_) {
      setState(() => _timeLeft = _remainingTime());
    });
  }

  @override
  void dispose() {
    _ticker?.cancel();
    super.dispose();
  }

  Duration _remainingTime() {
    final diff = _trialEndsAt.difference(DateTime.now());
    return diff.isNegative ? Duration.zero : diff;
  }

  String _formatRemaining(Duration duration) {
    final days = duration.inDays;
    final hours = duration.inHours % 24;
    final minutes = duration.inMinutes % 60;
    final seconds = duration.inSeconds % 60;

    final buffer = StringBuffer();
    if (days > 0) {
      buffer.write('${days}д ');
    }
    buffer
      ..write(hours.toString().padLeft(2, '0'))
      ..write(':')
      ..write(minutes.toString().padLeft(2, '0'))
      ..write(':')
      ..write(seconds.toString().padLeft(2, '0'));

    return buffer.toString();
    _planEntries = _seedPlan();
  }

  List<_AiPlanEntry> _seedPlan() {
    final now = DateTime.now();
    final base = DateTime(now.year, now.month, now.day);

    DateTime slot(int addDays, int hour, int minute) =>
        DateTime(base.year, base.month, base.day + addDays, hour, minute);

    return <_AiPlanEntry>[
      _AiPlanEntry(
        id: 'deep-work-1',
        title: 'Глубокая работа над стратегией',
        description: 'AI подобрал два часа фокуса под OKR Q4.',
        startAt: slot(0, 9, 0),
        endAt: slot(0, 11, 0),
        tags: const <String>['Фокус', 'OKR'],
      ),
      _AiPlanEntry(
        id: 'design-sync',
        title: 'Созвон с дизайнером',
        description: 'Флоу онбординга, выравнивание по макетам.',
        startAt: slot(0, 12, 0),
        endAt: slot(0, 12, 45),
        tags: const <String>['Дизайн', 'Созвон'],
      ),
      _AiPlanEntry(
        id: 'reporting',
        title: 'Подготовка квартального отчёта',
        description: 'Черновик для руководства, требует блок времени.',
        startAt: slot(0, 15, 0),
        endAt: slot(0, 17, 0),
        tags: const <String>['Аналитика'],
      ),
      _AiPlanEntry(
        id: '1-1',
        title: '1:1 с менеджером',
        description: 'План развития и обратная связь.',
        startAt: slot(1, 10, 0),
        endAt: slot(1, 10, 45),
        tags: const <String>['HR'],
      ),
      _AiPlanEntry(
        id: 'late-deep-work',
        title: 'Найти время на pet-project',
        description: 'Запрос пользователя сохранить вечерний слот.',
        startAt: slot(1, 20, 0),
        endAt: slot(1, 21, 30),
        tags: const <String>['Личное', 'Вне смены'],
      ),
    ];
  }

  Future<void> _startPlanning() async {
    setState(() => _isPlanning = true);

    await Future<void>.delayed(const Duration(seconds: 2));

    if (mounted) {
      setState(() {
        _isPlanning = false;
        _planEntries = _seedPlan();
      });
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('AI подготовил черновик плана недели'),
          duration: Duration(seconds: 2),
        ),
      );
    }
  }

  Future<void> _upgradeToPro() async {
    setState(() => _isUpgrading = true);

    // TODO: интегрировать с платёжным провайдером
    await Future<void>.delayed(const Duration(seconds: 2));

    if (mounted) {
      setState(() => _isUpgrading = false);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Перевод на оплату откроется в платёжном профиле (заглушка).'),
          duration: Duration(seconds: 2),
        ),
      );
    }
  }

  void _toggleEntry(String id, bool? value) {
    setState(() {
      _planEntries = _planEntries
          .map((entry) => entry.id == id ? entry.copyWith(selected: value ?? false) : entry)
          .toList();
    });
  }

  void _toggleAll(bool value) {
    setState(() {
      _planEntries = _planEntries.map((entry) => entry.copyWith(selected: value)).toList();
    });
  }

  void _rejectPlan() {
    setState(() {
      _planEntries = _planEntries.map((entry) => entry.copyWith(selected: false, committed: false)).toList();
    });
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('План отклонён. AI сможет предложить новую версию.')),
    );
  }

  Future<void> _applySelected() async {
    if (_isApplying) return;

    setState(() => _isApplying = true);
    final controller = ref.read(calendarControllerProvider.notifier);

    final selected = _planEntries.where((entry) => entry.selected && !entry.committed);
    for (final entry in selected) {
      await controller.addEvent(
        CalendarEventDraft(
          title: entry.title,
          description: entry.description,
          startAt: entry.startAt,
          endAt: entry.endAt,
        ),
      );
    }

    if (mounted) {
      setState(() {
        _isApplying = false;
        _planEntries = _planEntries
            .map(
              (entry) =>
                  entry.selected ? entry.copyWith(committed: true) : entry,
            )
            .toList();
      });
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Изменения отправлены в календарь')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final calendarState = ref.watch(calendarControllerProvider);

    final conflicts = _planEntries.where((entry) => _conflictFor(entry, calendarState.events) != null);
    final outsideShift =
        _planEntries.where((entry) => !_isWithinShift(entry.startAt, entry.endAt)).length;
    final applied = _planEntries.where((entry) => entry.committed).length;
    final selectedCount = _planEntries.where((entry) => entry.selected).length;

    return Scaffold(
      appBar: AppBar(title: const Text('Подписка и Trial')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            Text(
              'Статус подписки LifeMerge',
              style: theme.textTheme.headlineMedium,
            ),
            const SizedBox(height: 8),
            Text(
              'Следи за оставшимся временем Trial, смотри ограничения Free и оформи Pro, когда будешь готов.',
              style: theme.textTheme.bodyMedium,
            ),
            const SizedBox(height: 20),
            _TrialStatusCard(
              isTrialActive: _isTrialActive,
              formattedTimeLeft: _formatRemaining(_timeLeft),
              onUpgradeTap: _isUpgrading ? null : _upgradeToPro,
              isUpgrading: _isUpgrading,
            ),
            const SizedBox(height: 16),
            _FreeLimitationsCard(),
            const SizedBox(height: 16),
            _ProBenefitsCard(onStartPlanning: _isPlanning ? null : _startPlanning, isPlanning: _isPlanning),
          ],
        ),
      ),
    );
  }
}

class _TrialStatusCard extends StatelessWidget {
  const _TrialStatusCard({
    required this.isTrialActive,
    required this.formattedTimeLeft,
    required this.onUpgradeTap,
    required this.isUpgrading,
  });

  final bool isTrialActive;
  final String formattedTimeLeft;
  final VoidCallback? onUpgradeTap;
  final bool isUpgrading;
      appBar: AppBar(title: const Text('AI-план: предпросмотр')),
      body: RefreshIndicator(
        onRefresh: () => ref.read(calendarControllerProvider.notifier).refresh(),
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: <Widget>[
              Text(
                'AI предлагает расставить задачи и встречи по рабочим сменам.',
                style: theme.textTheme.headlineSmall,
              ),
              const SizedBox(height: 8),
              Text(
                'Выберите, что принять полностью или частично, отклоните ненужное и отправьте в календарь. '
                'Конфликты подсвечены, как и слоты вне рабочей смены.',
                style: theme.textTheme.bodyMedium,
              ),
              const SizedBox(height: 16),
              _PlanningStateCard(
                isPlanning: _isPlanning,
                onStartPlanning: _startPlanning,
                onTrial: _showTrialInfo,
                trialRequested: _trialRequested,
                pendingCount: calendarState.pendingOperations.length,
              ),
              const SizedBox(height: 16),
              _PlanSummary(
                conflicts: conflicts.length,
                outsideShift: outsideShift,
                applied: applied,
                selected: selectedCount,
              ),
              const SizedBox(height: 12),
              Card(
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      Row(
                        children: <Widget>[
                          Expanded(
                            child: Text(
                              'Рабочие смены',
                              style: theme.textTheme.titleMedium,
                            ),
                          ),
                          FilledButton.tonalIcon(
                            onPressed: () => _toggleAll(true),
                            icon: const Icon(Icons.done_all_outlined),
                            label: const Text('Принять всё'),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: const <Widget>[
                          _ShiftChip(label: 'Пн–Пт 09:00–18:00', icon: Icons.schedule),
                          _ShiftChip(label: 'Фокус 09:00–12:00', icon: Icons.bolt_outlined),
                          _ShiftChip(label: 'Вечер вне смены 18:00+', icon: Icons.nights_stay_outlined),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
              ..._planEntries.map(
                (entry) => Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: _PlanEntryCard(
                    entry: entry,
                    conflict: _conflictFor(entry, calendarState.events),
                    withinShift: _isWithinShift(entry.startAt, entry.endAt),
                    onToggle: (value) => _toggleEntry(entry.id, value),
                  ),
                ),
              ),
              const SizedBox(height: 8),
              Row(
                children: <Widget>[
                  Expanded(
                    child: FilledButton.icon(
                      onPressed: selectedCount == 0 || _isApplying
                          ? null
                          : _applySelected,
                      icon: _isApplying
                          ? const SizedBox(
                              height: 18,
                              width: 18,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : const Icon(Icons.event_available_outlined),
                      label: Text(
                        _isApplying
                            ? 'Отправляем в календарь'
                            : 'Применить выбранные (${selectedCount.clamp(0, _planEntries.length)})',
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  IconButton(
                    tooltip: 'Отклонить план',
                    icon: const Icon(Icons.close),
                    onPressed: _rejectPlan,
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  String? _conflictFor(_AiPlanEntry entry, List<CalendarEvent> events) {
    for (final event in events) {
      final eventEnd = event.endAt ?? event.startAt.add(const Duration(hours: 1));
      final hasConflict = _intersects(entry.startAt, entry.endAt, event.startAt, eventEnd);
      if (hasConflict) {
        return 'Конфликт с \'${event.title}\'';
      }
    }
    return null;
  }

  bool _intersects(
    DateTime startA,
    DateTime endA,
    DateTime startB,
    DateTime endB,
  ) {
    return startA.isBefore(endB) && endA.isAfter(startB);
  }

  bool _isWithinShift(DateTime start, DateTime end) {
    final inStart = start.hour >= 9 && start.hour < 18;
    final inEnd = end.hour <= 18 || (end.hour == 18 && end.minute == 0);
    return inStart && inEnd;
  }
}

class _PlanEntryCard extends StatelessWidget {
  const _PlanEntryCard({
    required this.entry,
    required this.conflict,
    required this.withinShift,
    required this.onToggle,
  });

  final _AiPlanEntry entry;
  final String? conflict;
  final bool withinShift;
  final ValueChanged<bool?> onToggle;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return Card(
      elevation: 0,
      color: colorScheme.surface,

    final color = conflict != null
        ? theme.colorScheme.errorContainer
        : withinShift
            ? theme.colorScheme.secondaryContainer
            : theme.colorScheme.surfaceVariant;

    final textColor = conflict != null
        ? theme.colorScheme.onErrorContainer
        : withinShift
            ? theme.colorScheme.onSecondaryContainer
            : theme.colorScheme.onSurfaceVariant;

    return AnimatedContainer(
      duration: const Duration(milliseconds: 200),
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: conflict != null
              ? theme.colorScheme.error
              : withinShift
                  ? theme.colorScheme.secondary
                  : theme.colorScheme.outlineVariant,
        ),
      ),
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Checkbox(value: entry.selected, onChanged: onToggle),
              const SizedBox(width: 8),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Row(
                      children: <Widget>[
                        Expanded(
                          child: Text(
                            entry.title,
                            style: theme.textTheme.titleMedium?.copyWith(color: textColor),
                          ),
                        ),
                        if (entry.committed)
                          Icon(Icons.event_available, color: theme.colorScheme.primary),
                      ],
                    ),
                    const SizedBox(height: 4),
                    Text(entry.description, style: theme.textTheme.bodySmall?.copyWith(color: textColor)),
                    const SizedBox(height: 8),
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: <Widget>[
                        _Pill(
                          icon: Icons.schedule,
                          label: _formatRange(entry.startAt, entry.endAt),
                          background: Colors.transparent,
                          foreground: textColor,
                          borderColor: textColor.withOpacity(0.4),
                        ),
                        if (conflict != null)
                          _Pill(
                            icon: Icons.warning_amber_outlined,
                            label: conflict!,
                            background: theme.colorScheme.error,
                            foreground: theme.colorScheme.onError,
                          ),
                        if (!withinShift)
                          _Pill(
                            icon: Icons.nightlight_outlined,
                            label: 'Вне рабочей смены',
                            background: theme.colorScheme.tertiaryContainer,
                            foreground: theme.colorScheme.onTertiaryContainer,
                          )
                        else
                          _Pill(
                            icon: Icons.bolt_outlined,
                            label: 'В рабочей смене',
                            background: theme.colorScheme.primaryContainer,
                            foreground: theme.colorScheme.onPrimaryContainer,
                          ),
                        ...entry.tags.map(
                          (tag) => _Pill(
                            icon: Icons.label_outline,
                            label: tag,
                            background: Colors.transparent,
                            foreground: textColor,
                            borderColor: textColor.withOpacity(0.4),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  String _formatRange(DateTime start, DateTime end) {
    final dayLabel = _weekdayLabel(start.weekday);
    final startTime = '${start.hour.toString().padLeft(2, '0')}:${start.minute.toString().padLeft(2, '0')}';
    final endTime = '${end.hour.toString().padLeft(2, '0')}:${end.minute.toString().padLeft(2, '0')}';
    return '$dayLabel, $startTime–$endTime';
  }

  String _weekdayLabel(int weekday) {
    switch (weekday) {
      case DateTime.monday:
        return 'Пн';
      case DateTime.tuesday:
        return 'Вт';
      case DateTime.wednesday:
        return 'Ср';
      case DateTime.thursday:
        return 'Чт';
      case DateTime.friday:
        return 'Пт';
      case DateTime.saturday:
        return 'Сб';
      case DateTime.sunday:
        return 'Вс';
    }
    return '';
  }
}

class _AiPlanEntry {
  const _AiPlanEntry({
    required this.id,
    required this.title,
    required this.description,
    required this.startAt,
    required this.endAt,
    this.tags = const <String>[],
    this.selected = true,
    this.committed = false,
  });

  final String id;
  final String title;
  final String description;
  final DateTime startAt;
  final DateTime endAt;
  final List<String> tags;
  final bool selected;
  final bool committed;

  _AiPlanEntry copyWith({
    String? id,
    String? title,
    String? description,
    DateTime? startAt,
    DateTime? endAt,
    List<String>? tags,
    bool? selected,
    bool? committed,
  }) {
    return _AiPlanEntry(
      id: id ?? this.id,
      title: title ?? this.title,
      description: description ?? this.description,
      startAt: startAt ?? this.startAt,
      endAt: endAt ?? this.endAt,
      tags: tags ?? this.tags,
      selected: selected ?? this.selected,
      committed: committed ?? this.committed,
    );
  }
}

class _PlanningStateCard extends StatelessWidget {
  const _PlanningStateCard({
    required this.isPlanning,
    required this.onStartPlanning,
    required this.onTrial,
    required this.trialRequested,
    required this.pendingCount,
  });

  final bool isPlanning;
  final VoidCallback onStartPlanning;
  final VoidCallback onTrial;
  final bool trialRequested;
  final int pendingCount;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      elevation: 0,
      color: theme.colorScheme.surface,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Row(
              children: <Widget>[
                Icon(
                  isTrialActive ? Icons.timelapse_outlined : Icons.hourglass_disabled_outlined,
                  color: isTrialActive ? colorScheme.primary : colorScheme.onSurfaceVariant,
                ),
                Icon(Icons.auto_awesome, color: theme.colorScheme.primary),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      Text(
                        isTrialActive ? 'Trial активен' : 'Trial завершён',
                        style: theme.textTheme.titleMedium,
                      ),
                      const SizedBox(height: 4),
                      Text(
                        isTrialActive
                            ? 'Полный доступ к Pro ещё действует. Не забудь оформить подписку, чтобы не потерять функции.'
                            : 'Триал закончился. Оформи Pro, чтобы вернуть AI и синхронизацию.',
                      Text('AI план готов', style: theme.textTheme.titleMedium),
                      Text(
                        'Черновик учитывает занятость календаря и рабочие смены.',
                        style: theme.textTheme.bodySmall,
                      ),
                    ],
                  ),
                ),
                if (isTrialActive)
                  Chip(
                    label: Text('осталось $formattedTimeLeft'),
                    avatar: const Icon(Icons.timer_outlined, size: 18),
                if (pendingCount > 0)
                  Chip(
                    label: Text('Очередь: $pendingCount'),
                    avatar: const Icon(Icons.sync_problem_outlined),
                  ),
              ],
            ),
            const SizedBox(height: 12),
            if (!isTrialActive)
              Row(
                children: <Widget>[
                  Icon(Icons.lock_clock, color: colorScheme.error),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'AI-планировщик и автосинхронизация недоступны. Перейди на Pro, чтобы включить их снова.',
                      style: theme.textTheme.bodyMedium,
                    ),
                  ),
                ],
              ),
            const SizedBox(height: 12),
            FilledButton.icon(
              onPressed: onUpgradeTap,
              icon: isUpgrading
                  ? const SizedBox(
                      height: 16,
                      width: 16,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.workspace_premium_outlined),
              label: Text(isUpgrading ? 'Открываем оплату...' : 'Перейти на Pro'),
            ),
          ],
        ),
      ),
    );
  }
}

class _FreeLimitationsCard extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return Card(
      elevation: 0,
      color: colorScheme.surface,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Row(
              children: <Widget>[
                Icon(Icons.info_outline, color: colorScheme.secondary),
                const SizedBox(width: 8),
                Text('Ограничения Free', style: theme.textTheme.titleMedium),
              ],
            ),
            const SizedBox(height: 12),
            const _LimitationItem(
              icon: Icons.event_busy_outlined,
              title: 'Нет AI-планировщика',
              subtitle: 'Автоплан доступен только в Trial или Pro.',
            ),
            const SizedBox(height: 8),
            const _LimitationItem(
              icon: Icons.schedule_send_outlined,
              title: 'Синхронизация раз в 12 часов',
              subtitle: 'Pro держит календарь и задачи в реальном времени.',
            ),
            const SizedBox(height: 8),
            const _LimitationItem(
              icon: Icons.storage_outlined,
              title: 'История задач 30 дней',
              subtitle: 'В Pro нет ограничений по истории и скачиваниям.',
            ),
            const SizedBox(height: 8),
            const _LimitationItem(
              icon: Icons.shield_outlined,
              title: 'Без расширенных прав доступа',
              subtitle: 'Общий доступ к проектам и контроль прав — только в Pro.',
            ),
          ],
        ),
      ),
    );
  }
}

class _ProBenefitsCard extends StatelessWidget {
  const _ProBenefitsCard({
    required this.onStartPlanning,
    required this.isPlanning,
  });

  final VoidCallback? onStartPlanning;
  final bool isPlanning;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return Card(
      elevation: 0,
      color: colorScheme.surface,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Row(
              children: <Widget>[
                Icon(Icons.auto_awesome, color: colorScheme.primary),
                const SizedBox(width: 8),
                Text('Что даёт Pro', style: theme.textTheme.titleMedium),
              ],
            ),
            const SizedBox(height: 12),
            const _LimitationItem(
              icon: Icons.bolt_outlined,
              title: 'AI-план недели',
              subtitle: 'Расставит задачи по приоритету и календарю за секунды.',
            ),
            const SizedBox(height: 8),
            const _LimitationItem(
              icon: Icons.sync_lock_outlined,
              title: 'Мгновенная синхронизация',
              subtitle: 'Календарь, задачи и инбокс синкаются без задержек.',
            ),
            const SizedBox(height: 8),
            const _LimitationItem(
              icon: Icons.verified_user_outlined,
              title: 'Приоритетная поддержка',
              subtitle: 'Ответ за 2 часа и помощь в настройке интеграций.',
            ),
            const SizedBox(height: 12),
            FilledButton.icon(
              onPressed: onStartPlanning,
              icon: isPlanning
                  ? const SizedBox(
                      height: 16,
                      width: 16,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.play_arrow_rounded),
              label: Text(isPlanning ? 'AI считает план...' : 'Попробовать AI прямо сейчас'),
            ),
            Row(
              children: <Widget>[
                Expanded(
                  child: FilledButton.icon(
                    onPressed: isPlanning ? null : onStartPlanning,
                    icon: const Icon(Icons.auto_awesome_motion),
                    label: Text(isPlanning ? 'AI считает...' : 'Пересчитать план'),
                  ),
                ),
                const SizedBox(width: 12),
                OutlinedButton.icon(
                  onPressed: isPlanning ? null : onTrial,
                  icon: const Icon(Icons.workspace_premium_outlined),
                  label: Text(trialRequested ? 'Trial активируется' : 'Оформить Trial'),
                ),
              ],
            ),
            if (isPlanning) ...<Widget>[
              const SizedBox(height: 12),
              Row(
                children: <Widget>[
                  SizedBox(
                    height: 20,
                    width: 20,
                    child: CircularProgressIndicator(
                      strokeWidth: 3,
                      color: colorScheme.primary,
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      'Собираем задачи и календарь, чтобы построить оптимальный план.',
                      style: theme.textTheme.bodySmall,
                    ),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _LimitationItem extends StatelessWidget {
  const _LimitationItem({
    required this.icon,
    required this.title,
    required this.subtitle,
                  const SizedBox(
                    height: 24,
                    width: 24,
                    child: CircularProgressIndicator(strokeWidth: 3),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      'AI обновляет черновик под новые ограничения и календарь...',
                      style: theme.textTheme.bodyMedium,
                    ),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _PlanSummary extends StatelessWidget {
  const _PlanSummary({
    required this.conflicts,
    required this.outsideShift,
    required this.applied,
    required this.selected,
  });

  final int conflicts;
  final int outsideShift;
  final int applied;
  final int selected;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text('Итоги AI-плана', style: theme.textTheme.titleMedium),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: <Widget>[
                _SummaryChip(
                  label: 'Выбрано',
                  value: '$selected слотов',
                  icon: Icons.fact_check_outlined,
                  color: theme.colorScheme.primaryContainer,
                  textColor: theme.colorScheme.onPrimaryContainer,
                ),
                _SummaryChip(
                  label: 'Конфликтов',
                  value: '$conflicts',
                  icon: Icons.warning_amber_outlined,
                  color: conflicts > 0
                      ? theme.colorScheme.errorContainer
                      : theme.colorScheme.secondaryContainer,
                  textColor: conflicts > 0
                      ? theme.colorScheme.onErrorContainer
                      : theme.colorScheme.onSecondaryContainer,
                ),
                _SummaryChip(
                  label: 'Вне смены',
                  value: '$outsideShift',
                  icon: Icons.nightlight_outlined,
                  color: theme.colorScheme.tertiaryContainer,
                  textColor: theme.colorScheme.onTertiaryContainer,
                ),
                _SummaryChip(
                  label: 'Уже в календаре',
                  value: '$applied',
                  icon: Icons.event_available_outlined,
                  color: theme.colorScheme.surfaceVariant,
                  textColor: theme.colorScheme.onSurfaceVariant,
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _SummaryChip extends StatelessWidget {
  const _SummaryChip({
    required this.label,
    required this.value,
    required this.icon,
    required this.color,
    required this.textColor,
  });

  final String label;
  final String value;
  final IconData icon;
  final Color color;
  final Color textColor;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          Icon(icon, color: textColor),
          const SizedBox(width: 8),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Text(label, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: textColor)),
              Text(value, style: Theme.of(context).textTheme.titleMedium?.copyWith(color: textColor)),
            ],
          ),
        ],
      ),
    );
  }
}

class _Pill extends StatelessWidget {
  const _Pill({
    required this.icon,
    required this.label,
    required this.background,
    required this.foreground,
    this.borderColor,
  });

  final IconData icon;
  final String label;
  final Color background;
  final Color foreground;
  final Color? borderColor;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: background,
        borderRadius: BorderRadius.circular(20),
        border: borderColor != null ? Border.all(color: borderColor!) : null,
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          Icon(icon, size: 16, color: foreground),
          const SizedBox(width: 6),
          Text(label, style: TextStyle(color: foreground)),
        ],
      ),
    );
  }
}

class _ShiftChip extends StatelessWidget {
  const _ShiftChip({required this.label, required this.icon});

  final String label;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceVariant,
        borderRadius: BorderRadius.circular(24),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          Icon(icon, size: 18, color: theme.colorScheme.onSurfaceVariant),
          const SizedBox(width: 6),
          Text(label, style: TextStyle(color: theme.colorScheme.onSurfaceVariant)),
        ],
      ),
    );
  }
}
