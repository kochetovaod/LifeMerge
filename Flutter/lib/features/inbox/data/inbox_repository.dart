import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../domain/inbox_item.dart';

class InboxRepository {
  final List<InboxItem> _items = <InboxItem>[
    InboxItem(
      id: 'inbox-1',
      title: 'Согласовать план задач на неделю',
      note: 'Получено в чате, нужно разложить по задачам',
      capturedAt: DateTime.now().subtract(const Duration(hours: 2)),
    ),
    InboxItem(
      id: 'inbox-2',
      title: 'Подготовить материалы к встрече с инвестором',
      note: 'Слайды + резюме прогресса',
      capturedAt: DateTime.now().subtract(const Duration(hours: 5)),
    ),
    InboxItem(
      id: 'inbox-3',
      title: 'Забронировать зал на пятницу',
      note: 'Тренировка в 19:00, проверить расписание',
      capturedAt: DateTime.now().subtract(const Duration(days: 1)),
    ),
  ];

  Future<List<InboxItem>> fetchItems() async {
    await Future<void>.delayed(const Duration(milliseconds: 150));
    return List<InboxItem>.unmodifiable(_items);
  }

  Future<void> removeItem(String id) async {
    _items.removeWhere((item) => item.id == id);
  }

  Future<void> moveToEnd(String id) async {
    final index = _items.indexWhere((item) => item.id == id);
    if (index == -1) return;
    final item = _items.removeAt(index);
    _items.add(item);
  }
}

final inboxRepositoryProvider = Provider<InboxRepository>((ref) {
  return InboxRepository();
});
