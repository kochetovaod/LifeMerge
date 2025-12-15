import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../core/routing/routes.dart';

class OnboardingScreen extends StatefulWidget {
  const OnboardingScreen({super.key});

  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  final PageController _pageController = PageController();
  int _currentStep = 0;
  String? _customSchedule;
  String _selectedPreset = 'Стандартная пятидневка';
  bool _trialSkipped = false;

  final List<_SchedulePreset> _presets = const <_SchedulePreset>[
    _SchedulePreset(name: 'Стандартная пятидневка', shifts: 'Пн–Пт 9:00–18:00'),
    _SchedulePreset(name: 'Смены 2/2', shifts: '2 дня по 12ч, 2 выходных'),
    _SchedulePreset(name: 'Гибрид + вечер', shifts: 'Будни 12:00–20:00, суббота 10:00–15:00'),
  ];

  void _goTo(int index) {
    setState(() => _currentStep = index);
    _pageController.animateToPage(
      index,
      duration: const Duration(milliseconds: 300),
      curve: Curves.easeInOut,
    );
  }

  void _next() {
    if (_currentStep < 3) {
      _goTo(_currentStep + 1);
    } else {
      context.go(Routes.calendarDay);
    }
  }

  void _skipTrial() {
    setState(() => _trialSkipped = true);
    _next();
  }

  Widget _buildStepper() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: List.generate(4, (index) {
        final isActive = index == _currentStep;
        return AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          margin: const EdgeInsets.symmetric(horizontal: 4),
          height: 8,
          width: isActive ? 36 : 12,
          decoration: BoxDecoration(
            color: isActive ? Theme.of(context).colorScheme.primary : Theme.of(context).dividerColor,
            borderRadius: BorderRadius.circular(12),
          ),
        );
      }),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Добро пожаловать'),
        actions: <Widget>[
          if (_currentStep < 3)
            TextButton(
              onPressed: () => context.go(Routes.calendarDay),
              child: const Text('Пропустить'),
            ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: <Widget>[
            const SizedBox(height: 8),
            _buildStepper(),
            const SizedBox(height: 16),
            Expanded(
              child: PageView(
                controller: _pageController,
                physics: const NeverScrollableScrollPhysics(),
                children: <Widget>[
                  _StepCard(
                    title: 'Зачем LifeMerge',
                    subtitle:
                        'Синхронизируйте календарь, задачи, цели и финансы. Мастер подбирает смены и предлагает готовый план.',
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: const <Widget>[
                        _ValueTile(
                          icon: Icons.bolt,
                          title: 'AI планирование',
                          description: 'Подсказывает, когда сфокусироваться, а когда освободить окно под звонки.',
                        ),
                        SizedBox(height: 12),
                        _ValueTile(
                          icon: Icons.layers,
                          title: 'Единый бэклог',
                          description: 'Inbox→задача→календарь: ничего не теряется и всегда есть контекст.',
                        ),
                        SizedBox(height: 12),
                        _ValueTile(
                          icon: Icons.shield_moon,
                          title: 'Баланс смен и отдыха',
                          description: 'Шаблоны смен, буферы на дорогу и контроль перегрузок.',
                        ),
                      ],
                    ),
                    onNext: _next,
                  ),
                  _StepCard(
                    title: 'Выберите график',
                    subtitle: 'Можно взять пресет или настроить вручную: смены попадут в календарь.',
                    child: Column(
                      children: <Widget>[
                        ..._presets.map(
                          (preset) => RadioListTile<String>(
                            value: preset.name,
                            groupValue: _selectedPreset,
                            title: Text(preset.name),
                            subtitle: Text(preset.shifts),
                            onChanged: (value) => setState(() => _selectedPreset = value!),
                          ),
                        ),
                        const Divider(),
                        TextFormField(
                          decoration: const InputDecoration(
                            labelText: 'Свои смены',
                            hintText: 'Например: Пн–Ср 8:00–16:00, Сб 11:00–15:00',
                          ),
                          onChanged: (value) => setState(() => _customSchedule = value),
                        ),
                        const SizedBox(height: 12),
                        Align(
                          alignment: Alignment.centerLeft,
                          child: Text(
                            'Предпросмотр',
                            style: theme.textTheme.titleMedium,
                          ),
                        ),
                        const SizedBox(height: 8),
                        _CalendarPreview(schedule: _customSchedule ?? _selectedPreset),
                      ],
                    ),
                    onNext: _next,
                    onBack: () => _goTo(0),
                  ),
                  _StepCard(
                    title: 'Подключим задачи',
                    subtitle: 'Импортируйте бэклог и расставьте приоритеты. Можете отметить контекст и повторяемость.',
                    child: Column(
                      children: const <Widget>[
                        ListTile(
                          leading: CircleAvatar(child: Icon(Icons.cloud_download_outlined)),
                          title: Text('Импорт из календаря и таск-менеджеров'),
                          subtitle: Text('Google Calendar, Notion, Jira (заглушка).'),
                        ),
                        ListTile(
                          leading: CircleAvatar(child: Icon(Icons.flag_circle_outlined)),
                          title: Text('Цели и прогресс'),
                          subtitle: Text('Каждая задача может двигать цель. Покажем прогресс и дедлайны.'),
                        ),
                        ListTile(
                          leading: CircleAvatar(child: Icon(Icons.repeat)),
                          title: Text('Повторяемость и буферы'),
                          subtitle: Text('Напоминания, паузы между слотами и дорога до встречи.'),
                        ),
                      ],
                    ),
                    onNext: _next,
                    onBack: () => _goTo(1),
                  ),
                  _StepCard(
                    title: '7 дней Trial без карты',
                    subtitle:
                        'Получите AI расписание, видите пересечения и контроль бюджета. Можно пропустить и остаться на Free.',
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        if (_trialSkipped)
                          Container(
                            width: double.infinity,
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: theme.colorScheme.surfaceVariant,
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: const Text(
                              'Вы выбрали Free. Всегда можно включить Trial из профиля.',
                            ),
                          )
                        else
                          Card(
                            child: Padding(
                              padding: const EdgeInsets.all(16),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: const <Widget>[
                                  Text('Что даёт Trial', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                                  SizedBox(height: 8),
                                  _ValueTile(
                                    icon: Icons.auto_mode,
                                    title: 'AI-раскладка недели',
                                    description: 'Смены + дорога + задачи под уровень энергии.',
                                  ),
                                  SizedBox(height: 8),
                                  _ValueTile(
                                    icon: Icons.account_tree_outlined,
                                    title: 'Неограниченные проекты',
                                    description: 'Группировка задач по целям без лимитов.',
                                  ),
                                  SizedBox(height: 8),
                                  _ValueTile(
                                    icon: Icons.attach_money,
                                    title: 'Бюджет и регулярки',
                                    description: 'Синхронизация транзакций с календарём.',
                                  ),
                                ],
                              ),
                            ),
                          ),
                        const SizedBox(height: 12),
                        Wrap(
                          spacing: 8,
                          runSpacing: 8,
                          children: <Widget>[
                            FilledButton(
                              onPressed: _trialSkipped ? null : _next,
                              child: const Text('Запустить Trial'),
                            ),
                            OutlinedButton(
                              onPressed: _skipTrial,
                              child: Text(_trialSkipped ? 'Продолжить на Free' : 'Пропустить'),
                            ),
                          ],
                        ),
                      ],
                    ),
                    onNext: _next,
                    onBack: () => _goTo(2),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _StepCard extends StatelessWidget {
  const _StepCard({
    required this.title,
    required this.subtitle,
    required this.child,
    this.onNext,
    this.onBack,
  });

  final String title;
  final String subtitle;
  final Widget child;
  final VoidCallback? onNext;
  final VoidCallback? onBack;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Card(
        clipBehavior: Clip.hardEdge,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: <Widget>[
              Text(title, style: Theme.of(context).textTheme.headlineSmall),
              const SizedBox(height: 6),
              Text(subtitle, style: Theme.of(context).textTheme.bodyMedium),
              const SizedBox(height: 12),
              Expanded(child: SingleChildScrollView(child: child)),
              const SizedBox(height: 12),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: <Widget>[
                  if (onBack != null)
                    TextButton.icon(
                      onPressed: onBack,
                      icon: const Icon(Icons.chevron_left),
                      label: const Text('Назад'),
                    ),
                  const Spacer(),
                  if (onNext != null)
                    FilledButton.icon(
                      onPressed: onNext,
                      icon: const Icon(Icons.chevron_right),
                      label: const Text('Далее'),
                    ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ValueTile extends StatelessWidget {
  const _ValueTile({required this.icon, required this.title, required this.description});

  final IconData icon;
  final String title;
  final String description;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        CircleAvatar(
          radius: 18,
          backgroundColor: Theme.of(context).colorScheme.primary.withOpacity(0.1),
          child: Icon(icon, color: Theme.of(context).colorScheme.primary),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Text(title, style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 4),
              Text(description, style: Theme.of(context).textTheme.bodyMedium),
            ],
          ),
        ),
      ],
    );
  }
}

class _CalendarPreview extends StatelessWidget {
  const _CalendarPreview({required this.schedule});

  final String schedule;

  @override
  Widget build(BuildContext context) {
    final now = DateTime.now();
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Theme.of(context).dividerColor),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text('Неделя ${now.year}-${now.month.toString().padLeft(2, '0')}',
              style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: List.generate(5, (index) {
              final day = now.add(Duration(days: index));
              final label = '${day.day}.${day.month}';
              return Chip(
                avatar: const Icon(Icons.schedule, size: 16),
                label: Text('$label · смена 9:00–18:00'),
              );
            }),
          ),
          const SizedBox(height: 8),
          Text('План: $schedule', style: Theme.of(context).textTheme.bodySmall),
        ],
      ),
    );
  }
}

class _SchedulePreset {
  const _SchedulePreset({required this.name, required this.shifts});

  final String name;
  final String shifts;
}
