import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../domain/task.dart';
import 'tasks_api_service.dart';

class TasksRepository {
  TasksRepository(this._apiService);

  final TasksApiService _apiService;

  Future<List<Task>> fetchTasks() => _apiService.fetchTasks();

  Future<Task> createTask(Task task) => _apiService.createTask(task);

  Future<Task> updateTask(Task task) => _apiService.updateTask(task);

  Future<void> deleteTask(String id) => _apiService.deleteTask(id);
}

final tasksApiServiceProvider = Provider<TasksApiService>((ref) {
  return TasksApiService();
});

final tasksRepositoryProvider = Provider<TasksRepository>((ref) {
  final api = ref.read(tasksApiServiceProvider);
  return TasksRepository(api);
});
