import '../domain/task.dart';

enum TaskOperationType { create, update, delete }

class PendingTaskOperation {
  PendingTaskOperation({
    required this.type,
    required this.task,
    required this.requestId,
    required this.enqueuedAt,
  });

  final TaskOperationType type;
  final Task task;
  final String requestId;
  final DateTime enqueuedAt;
}

class TasksState {
  const TasksState({
    this.tasks = const <Task>[],
    this.isLoading = false,
    this.isOffline = false,
    this.pendingOperations = const <PendingTaskOperation>[],
    this.errorMessage,
  });

  final List<Task> tasks;
  final bool isLoading;
  final bool isOffline;
  final List<PendingTaskOperation> pendingOperations;
  final String? errorMessage;

  TasksState copyWith({
    List<Task>? tasks,
    bool? isLoading,
    bool? isOffline,
    List<PendingTaskOperation>? pendingOperations,
    String? errorMessage,
    bool clearError = false,
  }) {
    return TasksState(
      tasks: tasks ?? this.tasks,
      isLoading: isLoading ?? this.isLoading,
      isOffline: isOffline ?? this.isOffline,
      pendingOperations: pendingOperations ?? this.pendingOperations,
      errorMessage: clearError ? null : (errorMessage ?? this.errorMessage),
    );
  }
}
