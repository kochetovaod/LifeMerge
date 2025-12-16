import '../../../domain/entities/tasks/task.dart';

class TasksState {
  const TasksState({
    this.items = const <Task>[],
    this.isLoading = false,
    this.errorMessage,
  });

  final List<Task> items;
  final bool isLoading;
  final String? errorMessage;

  TasksState copyWith({
    List<Task>? items,
    bool? isLoading,
    String? errorMessage,
  }) {
    return TasksState(
      items: items ?? this.items,
      isLoading: isLoading ?? this.isLoading,
      errorMessage: errorMessage,
    );
  }
}
