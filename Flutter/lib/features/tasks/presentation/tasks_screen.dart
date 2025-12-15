import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../application/tasks_controller.dart';
import '../domain/task.dart';
import 'widgets/task_form_sheet.dart';
import 'widgets/task_list_item.dart';
import '../../../presentation/widgets/sync_status_banner.dart';

class TasksScreen extends ConsumerStatefulWidget {
  const TasksScreen({super.key});

  @override
  ConsumerState<TasksScreen> createState() => _TasksScreenState();
}

class _TasksScreenState extends ConsumerState<TasksScreen> {
  final Set<TaskPriority> _priorityFilter = TaskPriority.values.toSet();
  TaskStatus? _statusFilter;
  bool _groupByGoal = true;

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

  List<Task> _filtered(List<Task> tasks) {
    return tasks.where((task) {
      final matchesPriority = _priorityFilter.contains(task.priority);
      final matchesStatus = _statusFilter == null || task.status == _statusFilter;
      return matchesPriority && matchesStatus;
    }).toList();
  }

  Map<String, List<Task>> _grouped(List<Task> tasks) {
    if (!_groupByGoal) {
      return {'Все задачи': tasks};
    }
    final Map<String, List<Task>> groups = <String, List<Task>>{};
    for (final task in tasks) {
      final key = task.status == TaskStatus.done
          ? 'Завершено'
          : task.priority == TaskPriority.high
              ? 'Фокус'
              : 'Бэклог';
      groups.putIfAbsent(key, () => <Task>[]).add(task);
    }
    return groups;
  }

  void _toggleStatus(Task task, TaskStatus status) {
    final controller = ref.read(tasksControllerProvider.notifier);
    final draft = TaskDraft(
      title: task.title,
      description: task.description,
      dueAt: task.dueAt,
      priority: task.priority,
      estimatedMinutes: task.estimatedMinutes,
      energyLevel: task.energyLevel,
      status: status,
    );
    controller.updateTask(task, draft);
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(tasksControllerProvider);
    final controller = ref.read(tasksControllerProvider.notifier);
    final hasConflict = state.errorMessage?.toLowerCase().contains('conflict') ?? false;
    final queueItems = state.pendingOperations
        .map(
          (operation) => SyncQueueItem(
            id: operation.requestId,
            title: operation.task.title.isNotEmpty ? operation.task.title : 'Untitled task',
            description: _operationDescription(operation),
            enqueuedAt: operation.enqueuedAt,
            typeLabel: _operationLabel(operation.type),
            isConflict: hasConflict,
          ),
        )
        .toList();

    final filtered = _filtered(state.tasks);
    final grouped = _grouped(filtered);
    final completed = state.tasks.where((task) => task.status == TaskStatus.done).length;
    final progress = state.tasks.isEmpty ? 0.0 : completed / state.tasks.length;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Tasks & Goals'),
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
        label: const Text('Новая задача/цель'),
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
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Row(
                  children: <Widget>[
                    const Icon(Icons.flag_outlined),
                    const SizedBox(width: 8),
                    Expanded(
                      child: LinearProgressIndicator(value: progress),
                    ),
                    const SizedBox(width: 8),
                    Text('${(progress * 100).round()}% целей закрыто'),
                  ],
                ),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: <Widget>[
                    ...TaskPriority.values.map(
                      (priority) => FilterChip(
                        label: Text(priority.name),
                        selected: _priorityFilter.contains(priority),
                        onSelected: (selected) => setState(() {
                          if (selected) {
                            _priorityFilter.add(priority);
                          } else {
                            _priorityFilter.remove(priority);
                          }
                        }),
                      ),
                    ),
                    DropdownButton<TaskStatus?>(
                      value: _statusFilter,
                      hint: const Text('Статус'),
                      onChanged: (value) => setState(() => _statusFilter = value),
                      items: <DropdownMenuItem<TaskStatus?>>[
                        const DropdownMenuItem<TaskStatus?>(value: null, child: Text('Все')),
                        ...TaskStatus.values
                            .map((status) => DropdownMenuItem<TaskStatus?>(value: status, child: Text(status.name)))
                            .toList(),
                      ],
                    ),
                    FilterChip(
                      label: const Text('Группировать по цели/приоритету'),
                      selected: _groupByGoal,
                      onSelected: (value) => setState(() => _groupByGoal = value),
                    ),
                  ],
                ),
              ],
            ),
          ),
          Expanded(
            child: state.isLoading
                ? const Center(child: CircularProgressIndicator())
                : filtered.isEmpty
                    ? const _EmptyTasks()
                    : ListView(
                        children: grouped.entries
                            .map(
                              (entry) => Padding(
                                padding: const EdgeInsets.only(bottom: 12),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: <Widget>[
                                    Padding(
                                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                                      child: Row(
                                        children: <Widget>[
                                          Text(entry.key, style: Theme.of(context).textTheme.titleMedium),
                                          const Spacer(),
                                          Text('Задач: ${entry.value.length}'),
                                        ],
                                      ),
                                    ),
                                    ...entry.value.map(
                                      (task) => TaskListItem(
                                        task: task,
                                        onTap: () => _openForm(context, ref, task: task),
                                        onDelete: () => controller.deleteTask(task),
                                        onToggleStatus: (status) => _toggleStatus(task, status),
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            )
                            .toList(),
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
