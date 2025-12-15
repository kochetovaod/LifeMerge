import '../../../core/network/api_client.dart';
import '../../../domain/user.dart';
import '../domain/task.dart';

class TasksRepository {
  TasksRepository(this._apiClient);

  final ApiClient _apiClient;

  Future<List<Task>> fetchTasks() async {
    final data = await _apiClient.getTasks(limit: 50);
    final items = (data['items'] as List?) ?? (data['tasks'] as List?) ?? const <dynamic>[];
    return items.cast<Map<String, dynamic>>().map(Task.fromJson).toList();
  }

  Future<Task> createTask(TaskDraft draft) async {
    final data = await _apiClient.createTask(draft.toJson());
    final taskJson = (data['task'] as Map<String, dynamic>?) ?? data;
    return Task.fromJson(taskJson);
  }

  Future<Task> updateTask(String id, TaskDraft patch) async {
    final data = await _apiClient.updateTask(id, patch.toJson());
    final taskJson = (data['task'] as Map<String, dynamic>?) ?? data;
    return Task.fromJson(taskJson);
  }

  Future<void> deleteTask(String id) async {
    // твой ApiClient сейчас требует data в deleteTask (сомнительно).
    // оставляем пустой payload.
    await _apiClient.deleteTask(id, <String, dynamic>{});
  }
}
