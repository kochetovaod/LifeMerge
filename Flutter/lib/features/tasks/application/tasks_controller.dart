import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/di/providers.dart';
import '../data/tasks_cache.dart';
import '../data/tasks_repository.dart';
import '../domain/task.dart';
import 'tasks_state.dart';

class TasksController extends StateNotifier<TasksState> {
  TasksController(this._repo, this._cache) : super(const TasksState()) {
    // 1) покажем кэш сразу
    final cached = _cache.read();
    if (cached.isNotEmpty) {
      state = state.copyWith(items: cached);
    }
    // 2) потом обновим с сервера
    refresh();
  }

  final TasksRepository _repo;
  final TasksCache _cache;

  Future<void> refresh() async {
    state = state.copyWith(isLoading: true, errorMessage: null);
    try {
      final items = await _repo.fetchTasks();
      state = state.copyWith(items: items, isLoading: false);
      await _cache.write(items);
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
      await _cache.write(updated);
    } catch (e) {
      state = state.copyWith(isLoading: false, errorMessage: e.toString());
    }
  }

  Future<void> update(String id, TaskDraft patch) async {
    state = state.copyWith(isLoading: true, errorMessage: null);
    try {
      final updatedTask = await _repo.updateTask(id, patch);
      final updated = state.items.map((t) => t.id == id ? updatedTask : t).toList();
      state = state.copyWith(items: updated, isLoading: false);
      await _cache.write(updated);
    } catch (e) {
      state = state.copyWith(isLoading: false, errorMessage: e.toString());
    }
  }

  Future<void> remove(String id) async {
    // optimistic
    final before = state.items;
    final updated = before.where((t) => t.id != id).toList();
    state = state.copyWith(items: updated, errorMessage: null);
    await _cache.write(updated);

    try {
      await _repo.deleteTask(id);
    } catch (e) {
      // откат
      state = state.copyWith(items: before, errorMessage: e.toString());
      await _cache.write(before);
    }
  }
}
