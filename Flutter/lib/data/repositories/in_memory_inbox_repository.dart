import '../../domain/entities/inbox/inbox_goal.dart';
import '../../domain/entities/inbox/inbox_item.dart';
import '../../domain/repositories/inbox_repository.dart';

class InMemoryInboxRepository implements InboxRepository {
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

  @override
  Future<List<InboxItem>> fetchItems() async {
    await Future<void>.delayed(const Duration(milliseconds: 150));
    return List<InboxItem>.unmodifiable(_items);
  }

  @override
  Future<void> removeItem(String id) async {
    _items.removeWhere((item) => item.id == id);
  }

  @override
  Future<void> moveToEnd(String id) async {
    final index = _items.indexWhere((item) => item.id == id);
    if (index == -1) return;
    final item = _items.removeAt(index);
    _items.add(item);
  }

  @override
  Future<InboxGoal> saveGoal(GoalDraft draft, InboxItem source) async {
    final goal = InboxGoal(
      id: 'goal-${DateTime.now().microsecondsSinceEpoch}',
      title: draft.title,
      description: draft.description?.trim().isEmpty ?? true ? null : draft.description?.trim(),
      sourceItemId: source.id,
      createdAt: DateTime.now(),
    );
    await removeItem(source.id);
    return goal;
  }
}
