import 'package:flutter/material.dart';

class ProScreen extends StatefulWidget {
  const ProScreen({super.key});

  @override
  State<ProScreen> createState() => _ProScreenState();
}

class _ProScreenState extends State<ProScreen> {
  bool _isPlanning = false;
  bool _trialRequested = false;

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

  void _showTrialInfo() {
    setState(() => _trialRequested = true);
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Trial можно включить в настройках оплаты (заглушка).'),
        duration: Duration(seconds: 2),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('AI-планировщик')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            Text(
              'Сгенерируй план недели с помощью AI',
              style: theme.textTheme.headlineMedium,
            ),
            const SizedBox(height: 8),
            Text(
              'AI возьмёт ваши задачи и слоты в календаре, чтобы предложить оптимальный черновик. '
              'План доступен только в Pro или на время Trial.',
              style: theme.textTheme.bodyMedium,
            ),
            const SizedBox(height: 20),
            Card(
              elevation: 0,
              color: theme.colorScheme.surface,
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Row(
                      children: <Widget>[
                        Icon(Icons.workspace_premium_outlined,
                            color: theme.colorScheme.primary),
                        const SizedBox(width: 12),
                        Text(
                          'Доступно в Pro и Trial',
                          style: theme.textTheme.titleMedium,
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    const _RequirementItem(
                      icon: Icons.bolt_outlined,
                      title: '14 дней бесплатно',
                      subtitle: 'Запусти Trial, чтобы проверить AI-планирование без оплаты.',
                    ),
                    const SizedBox(height: 8),
                    const _RequirementItem(
                      icon: Icons.verified_user_outlined,
                      title: 'Нужна подписка Pro',
                      subtitle: 'Активные Pro-пользователи получают неограниченный доступ.',
                    ),
                    const SizedBox(height: 8),
                    const _RequirementItem(
                      icon: Icons.security_outlined,
                      title: 'Контроль и безопасность',
                      subtitle:
                          'План готовится на сервере. Мы соблюдаем ваши ограничения по времени и приватности.',
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 20),
            FilledButton.icon(
              onPressed: _isPlanning ? null : _startPlanning,
              icon: const Icon(Icons.auto_awesome),
              label: Text(_isPlanning ? 'AI считает план...' : 'Запустить AI-планирование'),
            ),
            const SizedBox(height: 12),
            OutlinedButton.icon(
              onPressed: _isPlanning ? null : _showTrialInfo,
              icon: const Icon(Icons.try_sms_star_outlined),
              label: Text(
                _trialRequested ? 'Запрос Trial отправлен' : 'Оформить Trial Pro',
              ),
            ),
            if (_isPlanning) ...<Widget>[
              const SizedBox(height: 20),
              Card(
                color: theme.colorScheme.primaryContainer.withOpacity(0.2),
                elevation: 0,
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Row(
                    children: <Widget>[
                      const SizedBox(
                        height: 24,
                        width: 24,
                        child: CircularProgressIndicator(strokeWidth: 3),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: <Widget>[
                            Text(
                              'AI готовит расписание',
                              style: theme.textTheme.titleMedium,
                            ),
                            const SizedBox(height: 4),
                            Text(
                              'Мы подбираем слоты под ваши задачи и календарь. Это займёт несколько секунд.',
                              style: theme.textTheme.bodySmall,
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _RequirementItem extends StatelessWidget {
  const _RequirementItem({
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
