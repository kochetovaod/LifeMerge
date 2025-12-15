import 'package:flutter/material.dart';

import '../../domain/task.dart';

class TaskListItem extends StatelessWidget {
  const TaskListItem({
    super.key,
    required this.task,
    this.onTap,
    this.onDelete,
    this.onToggleStatus,
  });

  final Task task;
  final VoidCallback? onTap;
  final VoidCallback? onDelete;
  final ValueChanged<TaskStatus>? onToggleStatus;

  Color _priorityColor(TaskPriority priority, BuildContext context) {
    switch (priority) {
      case TaskPriority.high:
        return Theme.of(context).colorScheme.error;
      case TaskPriority.medium:
        return Theme.of(context).colorScheme.primary;
      case TaskPriority.low:
        return Theme.of(context).colorScheme.secondary;
    }
  }

  String _statusLabel(TaskStatus status) {
    switch (status) {
      case TaskStatus.todo:
        return 'To do';
      case TaskStatus.inProgress:
        return 'In progress';
      case TaskStatus.done:
        return 'Done';
      case TaskStatus.deferred:
        return 'Deferred';
    }
  }

  @override
  Widget build(BuildContext context) {
    final dueText = task.dueAt != null
        ? 'Due ${MaterialLocalizations.of(context).formatShortDate(task.dueAt!)}'
        : 'No due date';
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Checkbox(
                value: task.status == TaskStatus.done,
                onChanged: onToggleStatus == null
                    ? null
                    : (value) => onToggleStatus!(value == true ? TaskStatus.done : TaskStatus.todo),
              ),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(
                      task.title,
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    if (task.description != null && task.description!.isNotEmpty)
                      Padding(
                        padding: const EdgeInsets.only(top: 4),
                        child: Text(
                          task.description!,
                          style: Theme.of(context).textTheme.bodyMedium,
                        ),
                      ),
                    Padding(
                      padding: const EdgeInsets.only(top: 8),
                      child: Wrap(
                        spacing: 8,
                        runSpacing: 4,
                        children: <Widget>[
                          Chip(
                            backgroundColor: _priorityColor(task.priority, context).withOpacity(0.15),
                            visualDensity: VisualDensity.compact,
                            label: Text('Prior: ${task.priority.name}'),
                          ),
                          Chip(
                            label: Text(_statusLabel(task.status)),
                            backgroundColor: Theme.of(context)
                                .colorScheme
                                .primaryContainer
                                .withOpacity(0.6),
                            visualDensity: VisualDensity.compact,
                          ),
                          Chip(
                            label: Text(dueText),
                            visualDensity: VisualDensity.compact,
                          ),
                          if (task.estimatedMinutes != null)
                            Chip(
                              label: Text('${task.estimatedMinutes} min'),
                              visualDensity: VisualDensity.compact,
                            ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              if (onDelete != null)
                IconButton(
                  icon: const Icon(Icons.delete_outline),
                  onPressed: onDelete,
                ),
            ],
          ),
        ),
      ),
    );
  }
}
