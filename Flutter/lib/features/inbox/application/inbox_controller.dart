import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/inbox_repository.dart';
import '../domain/inbox_goal.dart';
import '../domain/inbox_item.dart';
import 'inbox_state.dart';

class InboxController extends StateNotifier<InboxState> {
  InboxController(this._repository) : super(const InboxState()) {
    _loadItems();
  }

  final InboxRepository _repository;

  Future<void> _loadItems() async {
    state = state.copyWith(isLoading: true, clearError: true, currentIndex: 0);
    try {
      final items = await _repository.fetchItems();
      state = state.copyWith(isLoading: false, items: items, clearError: true, currentIndex: 0);
    } catch (error) {
      state = state.copyWith(isLoading: false, errorMessage: error.toString());
    }
  }

  Future<void> refresh() => _loadItems();

  Future<void> skipCurrent() async {
    final current = state.currentItem;
    if (current == null || state.items.length <= 1) return;
    await _repository.moveToEnd(current.id);
    final updatedItems = <InboxItem>[...state.items];
    final moved = updatedItems.removeAt(state.currentIndex);
    updatedItems.add(moved);
    state = state.copyWith(items: updatedItems, currentIndex: 0);
  }

  Future<void> completeCurrent() async {
    final current = state.currentItem;
    if (current == null) return;
    await _repository.removeItem(current.id);
    final updatedItems = <InboxItem>[...state.items]..removeAt(state.currentIndex);
    final newIndex = updatedItems.isEmpty
        ? 0
        : state.currentIndex.clamp(0, updatedItems.length - 1);
    state = state.copyWith(
      items: updatedItems,
      processedCount: state.processedCount + 1,
      currentIndex: newIndex,
    );
  }

  Future<void> saveGoal(GoalDraft draft) async {
    final current = state.currentItem;
    if (current == null) return;
    final goal = InboxGoal(
      id: 'goal-${DateTime.now().microsecondsSinceEpoch}',
      title: draft.title,
      description: draft.description?.trim().isEmpty ?? true ? null : draft.description?.trim(),
      sourceItemId: current.id,
      createdAt: DateTime.now(),
    );
    state = state.copyWith(convertedGoals: <InboxGoal>[...state.convertedGoals, goal]);
    await completeCurrent();
  }
}

final inboxControllerProvider = StateNotifierProvider<InboxController, InboxState>((ref) {
  final repository = ref.read(inboxRepositoryProvider);
  return InboxController(repository);
});
