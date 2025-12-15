import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/tasks_repository.dart';
import '../domain/task.dart';
import 'tasks_state.dart';

class TasksController extends StateNotifier<TasksState> {
  TasksController(this._repository) : super(const TasksState()) {
    _loadTasks();
  }

  final TasksRepository _repository;
  Timer? _retryTimer;

  Future<void> _loadTasks() async {
    state = state.copyWith(isLoading: true, clearError: true);
    await _flushQueue(force: true);
    try {
      final tasks = await _repository.fetchTasks();
      state = state.copyWith(tasks: tasks, isLoading: false, clearError: true);
    } catch (error) {
      state = state.copyWith(
        isLoading: false,
        errorMessage: error.toString(),
      );
    }
  }

  Future<void> refresh() => _loadTasks();

  Future<void> syncPending() async {
    await _flushQueue(force: true);
  }

  Future<void> addTask(TaskDraft draft) async {
    final now = DateTime.now();
    final pendingTask = Task(
      id: _generateRequestId(prefix: 'local'),
      title: draft.title,
      description: draft.description,
      dueAt: draft.dueAt,
      priority: draft.priority,
      estimatedMinutes: draft.estimatedMinutes,
      energyLevel: draft.energyLevel,
      status: draft.status,
      createdAt: now,
      updatedAt: now,
    );

    if (state.isOffline) {
      _enqueueOperation(TaskOperationType.create, pendingTask);
      _applyLocalChange(pendingTask);
      return;
    }

    await _executeCreate(pendingTask);
  }

  Future<void> updateTask(Task task, TaskDraft draft) async {
    final updatedTask = task.copyWith(
      title: draft.title,
      description: draft.description,
      dueAt: draft.dueAt,
      priority: draft.priority,
      estimatedMinutes: draft.estimatedMinutes,
      energyLevel: draft.energyLevel,
      status: draft.status,
      updatedAt: DateTime.now(),
    );

    if (state.isOffline) {
      _enqueueOperation(TaskOperationType.update, updatedTask);
      _replaceTask(task.id, updatedTask);
      return;
    }

    await _executeUpdate(updatedTask);
  }

  Future<void> deleteTask(Task task) async {
    final deletedTask = task.copyWith(deleted: true, updatedAt: DateTime.now());
    if (state.isOffline) {
      _enqueueOperation(TaskOperationType.delete, deletedTask);
      _removeTask(task.id);
      return;
    }

    await _executeDelete(deletedTask);
  }

  void toggleOfflineMode() {
    final wasOffline = state.isOffline;
    state = state.copyWith(isOffline: !state.isOffline);
    if (wasOffline && !state.isOffline) {
      unawaited(_flushQueue(force: true));
    }
  }

  void clearError() {
    if (state.errorMessage != null) {
      state = state.copyWith(clearError: true);
    }
  }

  void _applyLocalChange(Task task) {
    state = state.copyWith(tasks: <Task>[...state.tasks, task]);
  }

  void _replaceTask(String originalId, Task updated) {
    final tasks = state.tasks.map((task) {
      if (task.id == originalId) {
        return updated;
      }
      return task;
    }).toList();
    state = state.copyWith(tasks: tasks);
  }

  void _removeTask(String id) {
    state = state.copyWith(tasks: state.tasks.where((task) => task.id != id).toList());
  }

  void _enqueueOperation(TaskOperationType type, Task task) {
    final operation = PendingTaskOperation(
      type: type,
      task: task,
      requestId: _generateRequestId(),
      enqueuedAt: DateTime.now(),
    );
    state = state.copyWith(
      pendingOperations: <PendingTaskOperation>[...state.pendingOperations, operation],
    );
    _scheduleRetry();
  }

  Future<void> _flushQueue({bool force = false}) async {
    if (state.pendingOperations.isEmpty) {
      _cancelRetry();
      return;
    }

    if (state.isOffline && !force) {
      _scheduleRetry();
      return;
    }

    final List<PendingTaskOperation> remaining = <PendingTaskOperation>[];
    var hadError = false;
    for (final operation in state.pendingOperations) {
      try {
        switch (operation.type) {
          case TaskOperationType.create:
            final created = await _repository.createTask(operation.task);
            _replaceTask(operation.task.id, created);
            break;
          case TaskOperationType.update:
            final updated = await _repository.updateTask(operation.task);
            _replaceTask(operation.task.id, updated);
            break;
          case TaskOperationType.delete:
            await _repository.deleteTask(operation.task.id);
            _removeTask(operation.task.id);
            break;
        }
      } catch (error) {
        hadError = true;
        remaining.add(operation);
      }
    }

    state = state.copyWith(
      pendingOperations: remaining,
      isOffline: hadError && remaining.isNotEmpty,
    );

    if (remaining.isEmpty) {
      _cancelRetry();
    } else {
      _scheduleRetry();
    }
  }

  Future<void> _executeCreate(Task pendingTask) async {
    try {
      final created = await _repository.createTask(pendingTask);
      _applyOrInsert(created);
    } catch (error) {
      _enqueueOperation(TaskOperationType.create, pendingTask);
      state = state.copyWith(errorMessage: error.toString(), isOffline: true);
    }
  }

  Future<void> _executeUpdate(Task updatedTask) async {
    try {
      final updated = await _repository.updateTask(updatedTask);
      _replaceTask(updatedTask.id, updated);
    } catch (error) {
      _enqueueOperation(TaskOperationType.update, updatedTask);
      state = state.copyWith(errorMessage: error.toString(), isOffline: true);
    }
  }

  Future<void> _executeDelete(Task deletedTask) async {
    try {
      await _repository.deleteTask(deletedTask.id);
      _removeTask(deletedTask.id);
    } catch (error) {
      _enqueueOperation(TaskOperationType.delete, deletedTask);
      state = state.copyWith(errorMessage: error.toString(), isOffline: true);
    }
  }

  void _applyOrInsert(Task task) {
    final tasks = [...state.tasks];
    final index = tasks.indexWhere((element) => element.id == task.id);
    if (index == -1) {
      tasks.add(task);
    } else {
      tasks[index] = task;
    }
    state = state.copyWith(tasks: tasks);
  }

  String _generateRequestId({String prefix = 'req'}) {
    final timestamp = DateTime.now().microsecondsSinceEpoch;
    return '$prefix-$timestamp';
  }

  void _scheduleRetry() {
    _retryTimer ??= Timer.periodic(const Duration(seconds: 4), (_) {
      unawaited(_flushQueue(force: true));
    });
  }

  void _cancelRetry() {
    _retryTimer?.cancel();
    _retryTimer = null;
  }
}

final tasksControllerProvider = StateNotifierProvider<TasksController, TasksState>((ref) {
  final repository = ref.read(tasksRepositoryProvider);
  return TasksController(repository);
});
