import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../application/tasks_controller.dart';
import '../domain/task.dart';
import 'widgets/task_form_sheet.dart';
import 'widgets/task_list_item.dart';

class TasksScreen extends ConsumerWidget {
  const TasksScreen({super.key});

  void _openForm(BuildContext context, WidgetRef ref, {Task? task}) {
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      builder: (_) => TaskFormSheet(
        initialTask: task,
        onSubmit: (draft) {
          final controller = ref.read(tasksControllerProvider.notifier);
          if (task == null) {
            controller.addTask(draft);
          } else {
            controller.updateTask(task, draft);
          }
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(tasksControllerProvider);
    final controller = ref.read(tasksControllerProvider.notifier);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Tasks'),
        actions: <Widget>[
          IconButton(
            tooltip: state.isOffline ? 'Offline mode' : 'Go offline',
            icon: Stack(
              children: <Widget>[
                Icon(state.isOffline ? Icons.cloud_off : Icons.cloud_queue),
                if (state.pendingOperations.isNotEmpty)
                  Positioned(
                    right: 0,
                    top: 0,
                    child: CircleAvatar(
                      radius: 8,
                      backgroundColor: Theme.of(context).colorScheme.error,
                      child: Text(
                        state.pendingOperations.length.toString(),
                        style: const TextStyle(fontSize: 10, color: Colors.white),
                      ),
                    ),
                  ),
              ],
            ),
            onPressed: controller.toggleOfflineMode,
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: controller.refresh,
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        icon: const Icon(Icons.add_task),
        label: const Text('New task'),
        onPressed: () => _openForm(context, ref),
      ),
      body: Column(
        children: <Widget>[
          if (state.errorMessage != null)
            MaterialBanner(
              content: Text(state.errorMessage!),
              leading: const Icon(Icons.error_outline),
              actions: <Widget>[
                TextButton(
                  onPressed: controller.clearError,
                  child: const Text('Dismiss'),
                ),
              ],
            ),
          if (state.pendingOperations.isNotEmpty)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Row(
                children: <Widget>[
                  const Icon(Icons.sync_problem_outlined),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Queued: ${state.pendingOperations.length} ops waiting for connection',
                      style: Theme.of(context).textTheme.bodyMedium,
                    ),
                  ),
                  if (!state.isOffline)
                    TextButton(
                      onPressed: controller.syncPending,
                      child: const Text('Sync now'),
                    ),
                ],
              ),
            ),
          Expanded(
            child: state.isLoading
                ? const Center(child: CircularProgressIndicator())
                : state.tasks.isEmpty
                    ? const _EmptyTasks()
                    : ListView.builder(
                        itemCount: state.tasks.length,
                        itemBuilder: (context, index) {
                          final task = state.tasks[index];
                          return TaskListItem(
                            task: task,
                            onTap: () => _openForm(context, ref, task: task),
                            onDelete: () => controller.deleteTask(task),
                          );
                        },
                      ),
          ),
        ],
      ),
    );
  }
}

class _EmptyTasks extends StatelessWidget {
  const _EmptyTasks();

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: <Widget>[
          const Icon(Icons.check_circle_outline, size: 64),
          const SizedBox(height: 12),
          Text(
            'No tasks yet',
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: 4),
          Text(
            'Create your first task to start planning',
            style: Theme.of(context).textTheme.bodyMedium,
          ),
        ],
      ),
    );
  }
}
