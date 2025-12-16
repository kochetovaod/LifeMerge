import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../app/router/routes.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  String _schedule = 'Пятидневка 9:00–18:00';
  String _timezone = 'Europe/Moscow';
  ThemeMode _themeMode = ThemeMode.system;
  bool _offlineMode = false;
  final List<_Device> _devices = <_Device>[
    _Device(name: 'iPhone 15', status: 'online'),
    _Device(name: 'MacBook', status: 'offline'),
  ];

  void _toggleOffline(bool value) {
    setState(() => _offlineMode = value);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: const Text('Профиль и настройки')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: <Widget>[
          Card(
            child: ListTile(
              leading: CircleAvatar(
                backgroundColor: theme.colorScheme.primary.withOpacity(0.15),
                child: Icon(Icons.verified_user, color: theme.colorScheme.primary),
              ),
              title: const Text('Trial активен'),
              subtitle: const Text('Осталось 7 дней. Можно перейти на Free или оплатить.'),
              trailing: FilledButton(
                onPressed: () => context.push(Routes.pro),
                child: const Text('Управлять'),
              ),
            ),
          ),
          const SizedBox(height: 12),
          Card(
            child: Column(
              children: <Widget>[
                ListTile(
                  leading: const Icon(Icons.calendar_month),
                  title: const Text('График'),
                  subtitle: Text(_schedule),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () async {
                    final result = await showModalBottomSheet<String>(
                      context: context,
                      builder: (_) => _OptionSheet(
                        title: 'Выбери график',
                        options: const <String>[
                          'Пятидневка 9:00–18:00',
                          'Смены 2/2',
                          'Своя сетка',
                        ],
                      ),
                    );
                    if (result != null) setState(() => _schedule = result);
                  },
                ),
                const Divider(),
                ListTile(
                  leading: const Icon(Icons.public),
                  title: const Text('Часовой пояс'),
                  subtitle: Text(_timezone),
                  onTap: () async {
                    final result = await showModalBottomSheet<String>(
                      context: context,
                      builder: (_) => _OptionSheet(
                        title: 'Часовой пояс',
                        options: const <String>['Europe/Moscow', 'Europe/Berlin', 'Asia/Almaty'],
                      ),
                    );
                    if (result != null) setState(() => _timezone = result);
                  },
                ),
                const Divider(),
                ListTile(
                  leading: const Icon(Icons.color_lens_outlined),
                  title: const Text('Тема'),
                  subtitle: Text(_themeMode.name),
                  onTap: () async {
                    final result = await showModalBottomSheet<ThemeMode>(
                      context: context,
                      builder: (_) => _ThemeSheet(selected: _themeMode),
                    );
                    if (result != null) setState(() => _themeMode = result);
                  },
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),
          Card(
            child: Column(
              children: <Widget>[
                SwitchListTile(
                  title: const Text('Офлайн-режим'),
                  subtitle: const Text('Можно работать до 3 офлайн-сессий'),
                  value: _offlineMode,
                  onChanged: _toggleOffline,
                ),
                ListTile(
                  leading: const Icon(Icons.devices_other_outlined),
                  title: const Text('Устройства'),
                  subtitle: Text('Активно: ${_devices.length} из 3'),
                ),
                ..._devices.map(
                  (device) => ListTile(
                    leading: Icon(device.status == 'online' ? Icons.check_circle : Icons.cloud_off),
                    title: Text(device.name),
                    subtitle: Text('Статус: ${device.status}'),
                    trailing: TextButton(
                      onPressed: () => setState(() => _devices.remove(device)),
                      child: const Text('Разлогинить'),
                    ),
                  ),
                ),
                TextButton.icon(
                  onPressed: () => setState(() => _devices.add(_Device(name: 'Новая сессия', status: 'offline'))),
                  icon: const Icon(Icons.add),
                  label: const Text('Добавить офлайн-сессию'),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _OptionSheet extends StatelessWidget {
  const _OptionSheet({required this.title, required this.options});

  final String title;
  final List<String> options;

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          Padding(
            padding: const EdgeInsets.all(16),
            child: Text(title, style: Theme.of(context).textTheme.titleLarge),
          ),
          ...options.map(
            (option) => ListTile(
              title: Text(option),
              onTap: () => Navigator.of(context).pop(option),
            ),
          ),
        ],
      ),
    );
  }
}

class _ThemeSheet extends StatelessWidget {
  const _ThemeSheet({required this.selected});

  final ThemeMode selected;

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: ThemeMode.values
            .map(
              (mode) => RadioListTile<ThemeMode>(
                value: mode,
                groupValue: selected,
                title: Text(mode.name),
                onChanged: (value) => Navigator.of(context).pop(value),
              ),
            )
            .toList(),
      ),
    );
  }
}

class _Device {
  _Device({required this.name, required this.status});

  final String name;
  final String status;
}
