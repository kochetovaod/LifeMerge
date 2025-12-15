import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../tasks/application/tasks_controller.dart';
import '../../tasks/domain/task.dart';
import '../application/calendar_controller.dart';
import '../domain/calendar_event.dart';
import 'widgets/event_form_sheet.dart';

class CalendarDayScreen extends ConsumerStatefulWidget {
  const CalendarDayScreen({super.key});

  @override
  ConsumerState<CalendarDayScreen> createState() => _CalendarDayScreenState();
}

class _CalendarDayScreenState extends ConsumerState<CalendarDayScreen> {
  DateTime _selectedDay = DateTime.now();
  final ScrollController _timelineController = ScrollController();

  @override
  void dispose() {
    _timelineController.dispose();
    super.dispose();
  }

  void _changeDay(int offset) {
    setState(() {
      _selectedDay = _selectedDay.add(Duration(days: offset));
    });
  }

  void _openForm(
    BuildContext context,
    WidgetRef ref, {
    CalendarEvent? event,
    DateTime? startAt,
    DateTime? endAt,
    String? taskId,
    String? taskTitle,
  }) {
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      builder: (_) => EventFormSheet(
        initialEvent: event,
        initialStartAt: startAt,
        initialEndAt: endAt,
        initialTaskId: taskId,
        initialTaskTitle: taskTitle,
        onSubmit: (draft) {
          final controller = ref.read(calendarControllerProvider.notifier);
          if (event == null) {
            controller.addEvent(draft);
          } else {
            controller.updateEvent(event, draft);
          }
        },
      ),
    );
  }

  void _scheduleTaskOnSlot(Task task, DateTime slotStart) {
    final durationMinutes = task.estimatedMinutes ?? 60;
    final end = slotStart.add(Duration(minutes: durationMinutes));
    final calendarController = ref.read(calendarControllerProvider.notifier);
    final tasksController = ref.read(tasksControllerProvider.notifier);

    final draft = CalendarEventDraft(
      title: task.title,
      description: task.description,
      startAt: slotStart,
      endAt: end,
      taskId: task.id,
    );

    calendarController.addEvent(draft);

    final updateDraft = TaskDraft(
      title: task.title,
      description: task.description,
      dueAt: slotStart,
      priority: task.priority,
      estimatedMinutes: task.estimatedMinutes,
      energyLevel: task.energyLevel,
      status: TaskStatus.inProgress,
    );

    unawaited(tasksController.updateTask(task, updateDraft));

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          'Scheduled "${task.title}" at ${TimeOfDay.fromDateTime(slotStart).format(context)}',
        ),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  List<CalendarEvent> _eventsForDay(List<CalendarEvent> events) {
    return events
        .where((event) => _isSameDay(event.startAt, _selectedDay) && !event.deleted)
        .toList()
      ..sort((a, b) => a.startAt.compareTo(b.startAt));
  }

  bool _isSameDay(DateTime a, DateTime b) {
    return a.year == b.year && a.month == b.month && a.day == b.day;
  }

  DateTime _roundedStart(DateTime base) {
    final minute = base.minute;
    final remainder = minute % 30;
    final delta = remainder == 0 ? 0 : 30 - remainder;
    return DateTime(base.year, base.month, base.day, base.hour, minute + delta);
  }

  @override
  Widget build(BuildContext context) {
    final calendarState = ref.watch(calendarControllerProvider);
    final calendarController = ref.read(calendarControllerProvider.notifier);
    final tasksState = ref.watch(tasksControllerProvider);

    final events = _eventsForDay([...calendarState.events]);
    final tasks = tasksState.tasks
        .where((task) => !task.deleted && task.status != TaskStatus.done)
        .toList();
    final linkedEventsCount = events.where((event) => event.taskId != null).length;
    final tasksById = <String, Task>{for (final task in tasksState.tasks) task.id: task};

    final isWideLayout = MediaQuery.of(context).size.width >= 900;
    final today = DateTime.now();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Calendar'),
        actions: <Widget>[
          IconButton(
            tooltip: calendarState.isOffline ? 'Offline mode' : 'Go offline',
            icon: Stack(
              children: <Widget>[
                Icon(calendarState.isOffline ? Icons.cloud_off : Icons.cloud_queue),
                if (calendarState.pendingOperations.isNotEmpty)
                  Positioned(
                    right: 0,
                    top: 0,
                    child: CircleAvatar(
                      radius: 8,
                      backgroundColor: Theme.of(context).colorScheme.error,
                      child: Text(
                        calendarState.pendingOperations.length.toString(),
                        style: const TextStyle(fontSize: 10, color: Colors.white),
                      ),
                    ),
                  ),
              ],
            ),
            onPressed: calendarController.toggleOfflineMode,
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () {
              calendarController.refresh();
              ref.read(tasksControllerProvider.notifier).refresh();
            },
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        icon: const Icon(Icons.event),
        label: const Text('New event'),
        onPressed: () {
          final base = _isSameDay(today, _selectedDay)
              ? _roundedStart(DateTime.now())
              : DateTime(_selectedDay.year, _selectedDay.month, _selectedDay.day, 9);
          _openForm(context, ref, startAt: base, endAt: base.add(const Duration(hours: 1)));
        },
      ),
      body: Column(
        children: <Widget>[
          _DayHeader(
            selectedDay: _selectedDay,
            totalEvents: events.length,
            linkedEvents: linkedEventsCount,
            unscheduledTasks: tasks.length,
            onPrevious: () => _changeDay(-1),
            onNext: () => _changeDay(1),
          ),
          if (calendarState.errorMessage != null)
            MaterialBanner(
              content: Text(calendarState.errorMessage!),
              leading: const Icon(Icons.error_outline),
              actions: <Widget>[
                TextButton(
                  onPressed: calendarController.clearError,
                  child: const Text('Dismiss'),
                ),
              ],
            ),
          if (calendarState.pendingOperations.isNotEmpty)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Row(
                children: <Widget>[
                  const Icon(Icons.sync_problem_outlined),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Queued: ${calendarState.pendingOperations.length} changes waiting for connection',
                      style: Theme.of(context).textTheme.bodyMedium,
                    ),
                  ),
                  if (!calendarState.isOffline)
                    TextButton(
                      onPressed: calendarController.syncPending,
                      child: const Text('Sync now'),
                    ),
                ],
              ),
            ),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              child: isWideLayout
                  ? Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        SizedBox(
                          width: 320,
                          child: _TaskBoard(
                            tasks: tasks,
                            isLoading: tasksState.isLoading,
                            onTaskTap: (task) => _openForm(
                              context,
                              ref,
                              startAt: _roundedStart(DateTime.now()),
                              endAt: _roundedStart(DateTime.now()).add(const Duration(hours: 1)),
                              taskId: task.id,
                              taskTitle: task.title,
                            ),
                          ),
                        ),
                        const SizedBox(width: 16),
                        Expanded(
                          child: _DayTimeline(
                            day: _selectedDay,
                            controller: _timelineController,
                            events: events,
                            tasksById: tasksById,
                            onSlotTap: (slot) => _openForm(
                              context,
                              ref,
                              startAt: slot,
                              endAt: slot.add(const Duration(minutes: 45)),
                            ),
                            onTaskDropped: _scheduleTaskOnSlot,
                            onEdit: (event) => _openForm(
                              context,
                              ref,
                              event: event,
                              taskId: event.taskId,
                              taskTitle: tasksById[event.taskId]?.title,
                            ),
                            onDelete: calendarController.deleteEvent,
                          ),
                        ),
                      ],
                    )
                  : Column(
                      children: [
                        _TaskBoard(
                          tasks: tasks,
                          isLoading: tasksState.isLoading,
                          onTaskTap: (task) => _openForm(
                            context,
                            ref,
                            startAt: _roundedStart(DateTime.now()),
                            endAt: _roundedStart(DateTime.now()).add(const Duration(hours: 1)),
                            taskId: task.id,
                            taskTitle: task.title,
                          ),
                        ),
                        const SizedBox(height: 12),
                        Expanded(
                          child: _DayTimeline(
                            day: _selectedDay,
                            controller: _timelineController,
                            events: events,
                            tasksById: tasksById,
                            onSlotTap: (slot) => _openForm(
                              context,
                              ref,
                              startAt: slot,
                              endAt: slot.add(const Duration(minutes: 45)),
                            ),
                            onTaskDropped: _scheduleTaskOnSlot,
                            onEdit: (event) => _openForm(
                              context,
                              ref,
                              event: event,
                              taskId: event.taskId,
                              taskTitle: tasksById[event.taskId]?.title,
                            ),
                            onDelete: calendarController.deleteEvent,
                          ),
                        ),
                      ],
                    ),
            ),
          ),
        ],
      ),
    );
  }
}

class _DayHeader extends StatelessWidget {
  const _DayHeader({
    required this.selectedDay,
    required this.totalEvents,
    required this.linkedEvents,
    required this.unscheduledTasks,
    required this.onPrevious,
    required this.onNext,
  });

  final DateTime selectedDay;
  final int totalEvents;
  final int linkedEvents;
  final int unscheduledTasks;
  final VoidCallback onPrevious;
  final VoidCallback onNext;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final weekday = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][selectedDay.weekday - 1];
    final isToday = DateTime.now().year == selectedDay.year &&
        DateTime.now().month == selectedDay.month &&
        DateTime.now().day == selectedDay.day;
    final dateLabel = '${selectedDay.year}-${selectedDay.month.toString().padLeft(2, '0')}-${selectedDay.day.toString().padLeft(2, '0')}';

    return Container(
      width: double.infinity,
      margin: const EdgeInsets.all(12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            theme.colorScheme.primary.withOpacity(0.12),
            theme.colorScheme.secondary.withOpacity(0.1),
          ],
        ),
        borderRadius: BorderRadius.circular(18),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              IconButton(onPressed: onPrevious, icon: const Icon(Icons.chevron_left)),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('$weekday ${isToday ? '(today)' : ''}', style: theme.textTheme.titleMedium),
                  const SizedBox(height: 4),
                  Text(dateLabel, style: theme.textTheme.headlineSmall),
                ],
              ),
              IconButton(onPressed: onNext, icon: const Icon(Icons.chevron_right)),
              const Spacer(),
              FilledButton.icon(
                onPressed: onNext,
                icon: const Icon(Icons.navigate_next),
                label: const Text('Jump to next'),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 12,
            runSpacing: 8,
            children: [
              _StatChip(icon: Icons.event_available, label: 'Events', value: '$totalEvents'),
              _StatChip(icon: Icons.link, label: 'Linked tasks', value: '$linkedEvents'),
              _StatChip(icon: Icons.pending_actions, label: 'Inbox tasks', value: '$unscheduledTasks'),
            ],
          ),
        ],
      ),
    );
  }
}

class _StatChip extends StatelessWidget {
  const _StatChip({required this.icon, required this.label, required this.value});

  final IconData icon;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: theme.dividerColor),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 18),
          const SizedBox(width: 8),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(label, style: theme.textTheme.labelSmall),
              Text(value, style: theme.textTheme.titleMedium),
            ],
          ),
        ],
      ),
    );
  }
}

class _TaskBoard extends StatelessWidget {
  const _TaskBoard({
    required this.tasks,
    required this.isLoading,
    required this.onTaskTap,
  });

  final List<Task> tasks;
  final bool isLoading;
  final ValueChanged<Task> onTaskTap;

  Color _priorityColor(TaskPriority priority, ThemeData theme) {
    switch (priority) {
      case TaskPriority.high:
        return theme.colorScheme.errorContainer;
      case TaskPriority.medium:
        return theme.colorScheme.tertiaryContainer;
      case TaskPriority.low:
        return theme.colorScheme.secondaryContainer;
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.check_circle_outline),
                const SizedBox(width: 8),
                Text('Tasks to schedule', style: theme.textTheme.titleMedium),
                const Spacer(),
                if (isLoading) const SizedBox(height: 18, width: 18, child: CircularProgressIndicator(strokeWidth: 2)),
              ],
            ),
            const SizedBox(height: 12),
            if (tasks.isEmpty && !isLoading)
              Text(
                'Drag tasks into the timeline to book a slot.',
                style: theme.textTheme.bodyMedium,
              ),
            if (tasks.isNotEmpty)
              ...tasks.map(
                (task) => Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Draggable<Task>(
                    data: task,
                    feedback: Material(
                      elevation: 6,
                      color: Colors.transparent,
                      child: _TaskCard(
                        task: task,
                        priorityColor: _priorityColor(task.priority, theme),
                        compact: true,
                      ),
                    ),
                    childWhenDragging: Opacity(
                      opacity: 0.5,
                      child: _TaskCard(
                        task: task,
                        priorityColor: _priorityColor(task.priority, theme),
                      ),
                    ),
                    child: GestureDetector(
                      onTap: () => onTaskTap(task),
                      child: _TaskCard(
                        task: task,
                        priorityColor: _priorityColor(task.priority, theme),
                      ),
                    ),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _TaskCard extends StatelessWidget {
  const _TaskCard({
    required this.task,
    required this.priorityColor,
    this.compact = false,
  });

  final Task task;
  final Color priorityColor;
  final bool compact;

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
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceVariant,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: priorityColor.withOpacity(0.6)),
      ),
      width: compact ? 260 : double.infinity,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 10,
                height: 10,
                decoration: BoxDecoration(color: priorityColor, shape: BoxShape.circle),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  task.title,
                  style: theme.textTheme.titleSmall,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              Text(_statusLabel(task.status), style: theme.textTheme.labelSmall),
            ],
          ),
          if (task.description != null && task.description!.isNotEmpty) ...[
            const SizedBox(height: 6),
            Text(task.description!, maxLines: 2, overflow: TextOverflow.ellipsis),
          ],
          if (task.estimatedMinutes != null)
            Padding(
              padding: const EdgeInsets.only(top: 6),
              child: Text('${task.estimatedMinutes} min', style: theme.textTheme.labelMedium),
            ),
        ],
      ),
    );
  }
}

class _DayTimeline extends StatelessWidget {
  const _DayTimeline({
    required this.day,
    required this.controller,
    required this.events,
    required this.tasksById,
    required this.onSlotTap,
    required this.onTaskDropped,
    required this.onEdit,
    required this.onDelete,
  });

  final DateTime day;
  final ScrollController controller;
  final List<CalendarEvent> events;
  final Map<String, Task> tasksById;
  final ValueChanged<DateTime> onSlotTap;
  final void Function(Task, DateTime) onTaskDropped;
  final ValueChanged<CalendarEvent> onEdit;
  final ValueChanged<CalendarEvent> onDelete;

  List<DateTime> _slots() {
    final start = DateTime(day.year, day.month, day.day);
    return List<DateTime>.generate(48, (index) => start.add(Duration(minutes: 30 * index)));
  }

  List<CalendarEvent> _eventsForSlot(DateTime slotStart) {
    final slotEnd = slotStart.add(const Duration(minutes: 30));
    return events.where((event) {
      final start = event.startAt;
      final end = event.endAt ?? event.startAt.add(const Duration(minutes: 45));
      return start.isBefore(slotEnd) && end.isAfter(slotStart);
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final slots = _slots();

    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: ListView.builder(
        controller: controller,
        itemCount: slots.length,
        itemBuilder: (context, index) {
          final slot = slots[index];
          final slotEvents = _eventsForSlot(slot);
          return DragTarget<Task>(
            onWillAccept: (_) => true,
            onAcceptWithDetails: (details) => onTaskDropped(details.data, slot),
            builder: (context, candidateData, rejectedData) {
              final isActive = candidateData.isNotEmpty;
              return InkWell(
                onTap: () => onSlotTap(slot),
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                  decoration: BoxDecoration(
                    color: isActive
                        ? theme.colorScheme.primaryContainer.withOpacity(0.35)
                        : theme.colorScheme.surface,
                    border: Border(
                      bottom: BorderSide(color: theme.dividerColor.withOpacity(0.4)),
                    ),
                  ),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      SizedBox(
                        width: 64,
                        child: Text(
                          TimeOfDay.fromDateTime(slot).format(context),
                          style: theme.textTheme.labelMedium,
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            if (slotEvents.isEmpty && !isActive)
                              Text(
                                'Drop a task or tap to add',
                                style: theme.textTheme.bodySmall,
                              ),
                            if (isActive)
                              Padding(
                                padding: const EdgeInsets.only(bottom: 4),
                                child: Row(
                                  children: [
                                    const Icon(Icons.downloading, size: 16),
                                    const SizedBox(width: 6),
                                    Text('Release to schedule task', style: theme.textTheme.labelMedium),
                                  ],
                                ),
                              ),
                            ...slotEvents.map(
                              (event) => Padding(
                                padding: const EdgeInsets.only(bottom: 6),
                                child: _EventCard(
                                  event: event,
                                  linkedTask: event.taskId != null ? tasksById[event.taskId] : null,
                                  onEdit: () => onEdit(event),
                                  onDelete: () => onDelete(event),
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }
}

class _EventCard extends StatelessWidget {
  const _EventCard({
    required this.event,
    this.linkedTask,
    required this.onEdit,
    required this.onDelete,
  });

  final CalendarEvent event;
  final Task? linkedTask;
  final VoidCallback onEdit;
  final VoidCallback onDelete;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final rangeLabel = _rangeLabel(context);
    return Container(
      decoration: BoxDecoration(
        color: linkedTask != null
            ? theme.colorScheme.secondaryContainer
            : theme.colorScheme.surfaceVariant,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: theme.dividerColor.withOpacity(0.4)),
      ),
      child: ListTile(
        dense: true,
        title: Text(event.title, style: theme.textTheme.titleSmall),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(rangeLabel),
            if (event.description != null && event.description!.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(top: 4),
                child: Text(event.description!, maxLines: 2, overflow: TextOverflow.ellipsis),
              ),
            if (linkedTask != null)
              Padding(
                padding: const EdgeInsets.only(top: 4),
                child: Row(
                  children: [
                    const Icon(Icons.link, size: 16),
                    const SizedBox(width: 6),
                    Expanded(
                      child: Text(
                        'Task: ${linkedTask!.title}',
                        style: theme.textTheme.labelMedium,
                      ),
                    ),
                  ],
                ),
              ),
          ],
        ),
        trailing: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            IconButton(
              tooltip: 'Edit',
              icon: const Icon(Icons.edit_outlined),
              onPressed: onEdit,
            ),
            IconButton(
              tooltip: 'Delete',
              icon: const Icon(Icons.delete_outline),
              onPressed: onDelete,
            ),
          ],
        ),
      ),
    );
  }

  String _rangeLabel(BuildContext context) {
    final start = TimeOfDay.fromDateTime(event.startAt.toLocal()).format(context);
    final end = TimeOfDay.fromDateTime((event.endAt ?? event.startAt).toLocal()).format(context);
    return '$start - $end';
  }
}
