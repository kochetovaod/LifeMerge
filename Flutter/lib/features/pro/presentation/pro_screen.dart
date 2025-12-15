import 'dart:async';

import 'package:flutter/material.dart';

class ProScreen extends StatefulWidget {
  const ProScreen({super.key});

  @override
  State<ProScreen> createState() => _ProScreenState();
}

class _ProScreenState extends State<ProScreen> {
  late final DateTime _trialEndsAt;
  late Duration _timeLeft;
  Timer? _ticker;
  bool _isPlanning = false;
  bool _isUpgrading = false;

  bool get _isTrialActive => _timeLeft > Duration.zero;

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
  }

  Future<void> _startPlanning() async {
    setState(() => _isPlanning = true);

    // TODO: replace with real AI planning call
    await Future<void>.delayed(const Duration(seconds: 2));

    if (mounted) {
      setState(() => _isPlanning = false);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('AI-план готовится... (stub)'),
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

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

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
                Icon(
                  isTrialActive ? Icons.timelapse_outlined : Icons.hourglass_disabled_outlined,
                  color: isTrialActive ? colorScheme.primary : colorScheme.onSurfaceVariant,
                ),
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
                        style: theme.textTheme.bodySmall,
                      ),
                    ],
                  ),
                ),
                if (isTrialActive)
                  Chip(
                    label: Text('осталось $formattedTimeLeft'),
                    avatar: const Icon(Icons.timer_outlined, size: 18),
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
  });

  final IconData icon;
  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Icon(icon, color: theme.colorScheme.primary),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Text(title, style: theme.textTheme.titleSmall),
              const SizedBox(height: 4),
              Text(subtitle, style: theme.textTheme.bodySmall),
            ],
          ),
        ),
      ],
    );
  }
}
