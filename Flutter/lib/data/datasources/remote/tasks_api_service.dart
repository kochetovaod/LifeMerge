import 'dart:async';

import '../../../domain/entities/tasks/task.dart';

class TasksApiService {
  TasksApiService() {
    final now = DateTime.now();
    _remoteTasks.addAll(<Task>[
      Task(
        id: _generateId(),
        title: 'Write planning doc',
        description: 'Draft sprint backlog and share with the team',
        dueAt: now.add(const Duration(days: 1)),
        priority: TaskPriority.high,
        estimatedMinutes: 90,
        status: TaskStatus.inProgress,
        createdAt: now.subtract(const Duration(days: 1)),
        updatedAt: now,
      ),
      Task(
        id: _generateId(),
        title: 'Review Tasks API',
        description: 'Double-check idempotency rules before release',
        dueAt: now.add(const Duration(days: 2)),
        priority: TaskPriority.medium,
        estimatedMinutes: 60,
        status: TaskStatus.todo,
        createdAt: now.subtract(const Duration(days: 2)),
        updatedAt: now,
      ),
    ]);
  }

  final List<Task> _remoteTasks = <Task>[];

  Future<List<Task>> fetchTasks() async {
    await Future<void>.delayed(const Duration(milliseconds: 500));
    return List<Task>.unmodifiable(_remoteTasks.where((task) => !task.deleted));
  }

  Future<Task> createTask(Task task) async {
    await Future<void>.delayed(const Duration(milliseconds: 400));
    final now = DateTime.now();
    final createdTask = task.copyWith(
      id: task.id.isEmpty || task.id.startsWith('local') ? _generateId() : task.id,
      createdAt: task.createdAt == task.updatedAt ? now : task.createdAt,
      updatedAt: now,
      deleted: false,
    );
    _remoteTasks.removeWhere((existing) => existing.id == createdTask.id);
    _remoteTasks.add(createdTask);
    return createdTask;
  }

  Future<Task> updateTask(Task task) async {
    await Future<void>.delayed(const Duration(milliseconds: 400));
    final current = _remoteTasks.firstWhere((item) => item.id == task.id, orElse: () => task);
    final updated = current.copyWith(
      title: task.title,
      description: task.description,
      dueAt: task.dueAt,
      priority: task.priority,
      estimatedMinutes: task.estimatedMinutes,
      energyLevel: task.energyLevel,
      status: task.status,
      updatedAt: DateTime.now(),
    );
    _remoteTasks.removeWhere((existing) => existing.id == updated.id);
    _remoteTasks.add(updated);
    return updated;
  }

  Future<void> deleteTask(String id) async {
    await Future<void>.delayed(const Duration(milliseconds: 300));
    final currentIndex = _remoteTasks.indexWhere((task) => task.id == id);
    if (currentIndex != -1) {
      final current = _remoteTasks[currentIndex];
      _remoteTasks[currentIndex] = current.copyWith(
        deleted: true,
        updatedAt: DateTime.now(),
      );
    }
  }

  String _generateId() => DateTime.now().microsecondsSinceEpoch.toString();
}
