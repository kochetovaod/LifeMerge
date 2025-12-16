import '../../domain/entities/tasks/task.dart';
import '../../domain/repositories/tasks_repository.dart';
import '../datasources/local/tasks_cache.dart';
import '../datasources/remote/api_client.dart';

class TasksRepositoryImpl implements TasksRepository {
  TasksRepositoryImpl(this._apiClient, this._cache);

  final ApiClient _apiClient;
  final TasksCache _cache;

  @override
  List<Task> readCachedTasks() => _cache.read();

  @override
  Future<void> cacheTasks(List<Task> tasks) => _cache.write(tasks);

  @override
  Future<List<Task>> fetchTasks() async {
    final data = await _apiClient.getTasks(limit: 50);
    final items = (data['items'] as List?) ?? (data['tasks'] as List?) ?? const <dynamic>[];
    final tasks = items.cast<Map<String, dynamic>>().map(Task.fromJson).toList();
    await cacheTasks(tasks);
    return tasks;
  }

  @override
  Future<Task> createTask(TaskDraft draft) async {
    final data = await _apiClient.createTask(draft.toJson());
    final taskJson = (data['task'] as Map<String, dynamic>?) ?? data;
    final created = Task.fromJson(taskJson);
    final updated = <Task>[created, ...readCachedTasks()];
    await cacheTasks(updated);
    return created;
  }

  @override
  Future<Task> updateTask(String id, TaskDraft patch) async {
    final data = await _apiClient.updateTask(id, patch.toJson());
    final taskJson = (data['task'] as Map<String, dynamic>?) ?? data;
    final updatedTask = Task.fromJson(taskJson);
    final updated = readCachedTasks().map((task) => task.id == id ? updatedTask : task).toList();
    await cacheTasks(updated);
    return updatedTask;
  }

  @override
  Future<void> deleteTask(String id) async {
    await _apiClient.deleteTask(id, <String, dynamic>{});
    final updated = readCachedTasks().where((task) => task.id != id).toList();
    await cacheTasks(updated);
  }
}
