import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../domain/entities/tasks/task.dart';
import '../../../domain/repositories/tasks_repository.dart';
import 'tasks_state.dart';

class TasksController extends StateNotifier<TasksState> {
  TasksController(this._repo) : super(const TasksState()) {
    final cached = _repo.readCachedTasks();
    if (cached.isNotEmpty) {
      state = state.copyWith(items: cached);
    }
    refresh();
  }

  final TasksRepository _repo;

  void clearError() {
    if (state.errorMessage != null) {
      state = state.copyWith(errorMessage: null);
    }
  }

  Future<void> refresh() async {
    state = state.copyWith(isLoading: true, errorMessage: null);
    try {
      final items = await _repo.fetchTasks();
      state = state.copyWith(items: items, isLoading: false);
    } catch (e) {
      state = state.copyWith(isLoading: false, errorMessage: e.toString());
    }
  }

  Future<void> create(TaskDraft draft) async {
    state = state.copyWith(isLoading: true, errorMessage: null);
    try {
      final created = await _repo.createTask(draft);
      final updated = <Task>[created, ...state.items];
      state = state.copyWith(items: updated, isLoading: false);
      await _repo.cacheTasks(updated);
    } catch (e) {
      state = state.copyWith(isLoading: false, errorMessage: e.toString());
    }
  }

  Future<void> addTask(TaskDraft draft) => create(draft);

  Future<void> update(String id, TaskDraft patch) async {
    state = state.copyWith(isLoading: true, errorMessage: null);
    try {
      final updatedTask = await _repo.updateTask(id, patch);
      final updated = state.items.map((t) => t.id == id ? updatedTask : t).toList();
      state = state.copyWith(items: updated, isLoading: false);
      await _repo.cacheTasks(updated);
    } catch (e) {
      state = state.copyWith(isLoading: false, errorMessage: e.toString());
    }
  }

  Future<void> updateTask(Task task, TaskDraft patch) => update(task.id, patch);

  Future<void> remove(String id) async {
    final before = state.items;
    final updated = before.where((t) => t.id != id).toList();
    state = state.copyWith(items: updated, errorMessage: null);
    await _repo.cacheTasks(updated);

    try {
      await _repo.deleteTask(id);
    } catch (e) {
      state = state.copyWith(items: before, errorMessage: e.toString());
      await _repo.cacheTasks(before);
    }
  }
}
