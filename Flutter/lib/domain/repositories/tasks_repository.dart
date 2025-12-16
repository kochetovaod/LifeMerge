import '../entities/tasks/task.dart';

abstract class TasksRepository {
  List<Task> readCachedTasks();
  Future<void> cacheTasks(List<Task> tasks);
  Future<List<Task>> fetchTasks();
  Future<Task> createTask(TaskDraft draft);
  Future<Task> updateTask(String id, TaskDraft patch);
  Future<void> deleteTask(String id);
}
