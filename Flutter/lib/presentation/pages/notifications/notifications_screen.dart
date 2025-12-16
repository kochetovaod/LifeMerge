import 'package:flutter/material.dart';

class NotificationsScreen extends StatefulWidget {
  const NotificationsScreen({super.key});

  @override
  State<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends State<NotificationsScreen> {
  bool _permissionsGranted = false;
  bool _offline = false;
  bool _syncing = false;
  Duration _reminderLead = const Duration(minutes: 15);
  final Map<String, bool> _channels = <String, bool>{
    'Смены и события': true,
    'Задачи и цели': true,
    'Финансы и бюджеты': false,
    'AI-советы': true,
  };

  Future<void> _requestPermission() async {
    await Future<void>.delayed(const Duration(milliseconds: 300));
    setState(() => _permissionsGranted = true);
  }

  Future<void> _syncNow() async {
    setState(() => _syncing = true);
    await Future<void>.delayed(const Duration(seconds: 1));
    setState(() => _syncing = false);
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Настройки пушей синхронизированы')),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: const Text('Уведомления')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: <Widget>[
          if (_offline)
            _StatusBanner(
              color: theme.colorScheme.errorContainer,
              icon: Icons.cloud_off,
              message: 'Офлайн режим: пуши будут отправлены после синка',
              trailing: TextButton(onPressed: () => setState(() => _offline = false), child: const Text('Вернуться онлайн')),
            ),
          if (_syncing)
            _StatusBanner(
              color: theme.colorScheme.tertiaryContainer,
              icon: Icons.sync,
              message: 'Синхронизация...',
              trailing: const SizedBox(height: 18, width: 18, child: CircularProgressIndicator(strokeWidth: 2)),
            ),
          Card(
            child: SwitchListTile(
              value: _permissionsGranted,
              title: const Text('Системные разрешения'),
              subtitle: const Text('Показываем запрос только один раз'),
              onChanged: (_) => _requestPermission(),
            ),
          ),
          const SizedBox(height: 12),
          Card(
            child: Column(
              children: <Widget>[
                ListTile(
                  title: const Text('Категории пушей'),
                  subtitle: const Text('Отключите то, что не нужно'),
                  trailing: IconButton(
                    icon: const Icon(Icons.refresh),
                    onPressed: _syncNow,
                  ),
                ),
                ..._channels.entries.map(
                  (entry) => SwitchListTile(
                    value: entry.value,
                    title: Text(entry.key),
                    subtitle: Text(entry.value ? 'Включено' : 'Выключено'),
                    onChanged: (value) => setState(() => _channels[entry.key] = value),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),
          Card(
            child: Column(
              children: <Widget>[
                ListTile(
                  title: const Text('Упреждающие напоминания'),
                  subtitle: Text('Напомнить за ${_reminderLead.inMinutes} минут'),
                ),
                Slider(
                  min: 5,
                  max: 120,
                  divisions: 23,
                  value: _reminderLead.inMinutes.toDouble(),
                  label: '${_reminderLead.inMinutes} минут',
                  onChanged: (value) => setState(() => _reminderLead = Duration(minutes: value.round())),
                ),
                Padding(
                  padding: const EdgeInsets.all(12),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: const <Widget>[
                      Text('Задачи → 15 минут заранее'),
                      SizedBox(height: 4),
                      Text('События с дорогой → 30 минут заранее'),
                      SizedBox(height: 4),
                      Text('Смены → за 1 час'),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _StatusBanner extends StatelessWidget {
  const _StatusBanner({
    required this.color,
    required this.icon,
    required this.message,
    this.trailing,
  });

  final Color color;
  final IconData icon;
  final String message;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: <Widget>[
          Icon(icon),
          const SizedBox(width: 8),
          Expanded(child: Text(message)),
          if (trailing != null) trailing!,
        ],
      ),
    );
  }
}
