import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../application/tasks_controller.dart';
import '../domain/task.dart';
import 'widgets/task_form_sheet.dart';
import 'widgets/task_list_item.dart';
import '../../../presentation/widgets/sync_status_banner.dart';

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
    final hasConflict = state.errorMessage?.toLowerCase().contains('conflict') ?? false;
    final queueItems = state.pendingOperations
        .map(
          (operation) => SyncQueueItem(
            id: operation.requestId,
            title: operation.task.title.isNotEmpty
                ? operation.task.title
                : 'Untitled task',
            description: _operationDescription(operation),
            enqueuedAt: operation.enqueuedAt,
            typeLabel: _operationLabel(operation.type),
            isConflict: hasConflict,
          ),
        )
        .toList();

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
          SyncStatusBanner(
            isOffline: state.isOffline,
            queueItems: queueItems,
            onSyncNow: controller.syncPending,
            errorMessage: state.errorMessage,
            onDismissError: controller.clearError,
            title: 'Tasks sync',
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

  String _operationLabel(TaskOperationType type) {
    switch (type) {
      case TaskOperationType.create:
        return 'Create';
      case TaskOperationType.update:
        return 'Update';
      case TaskOperationType.delete:
        return 'Delete';
    }
  }

  String _operationDescription(PendingTaskOperation operation) {
    final title = operation.task.title.isNotEmpty ? operation.task.title : 'task';
    switch (operation.type) {
      case TaskOperationType.create:
        return 'New task "$title" queued';
      case TaskOperationType.update:
        return 'Changes to "$title" will sync';
      case TaskOperationType.delete:
        return 'Delete "$title" when online';
    }
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
