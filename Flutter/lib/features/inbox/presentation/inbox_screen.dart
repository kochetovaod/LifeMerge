import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../calendar/application/calendar_controller.dart';
import '../../calendar/presentation/widgets/event_form_sheet.dart';
import '../../tasks/application/tasks_controller.dart';
import '../../tasks/presentation/widgets/task_form_sheet.dart';
import '../application/inbox_controller.dart';
import '../domain/inbox_goal.dart';
import '../domain/inbox_item.dart';
import 'widgets/goal_capture_sheet.dart';

class InboxScreen extends ConsumerWidget {
  const InboxScreen({super.key});

  void _showTaskSheet(BuildContext context, WidgetRef ref, InboxItem item) {
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      builder: (_) => TaskFormSheet(
        initialTitle: item.title,
        initialDescription: item.note,
        onSubmit: (draft) {
          ref.read(tasksControllerProvider.notifier).addTask(draft);
          ref.read(inboxControllerProvider.notifier).completeCurrent();
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Задача создана из Inbox')),
          );
        },
      ),
    );
  }

  void _showEventSheet(BuildContext context, WidgetRef ref, InboxItem item) {
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      builder: (_) => EventFormSheet(
        initialTitle: item.title,
        initialTaskTitle: item.note,
        onSubmit: (draft) {
          ref.read(calendarControllerProvider.notifier).addEvent(draft);
          ref.read(inboxControllerProvider.notifier).completeCurrent();
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Событие создано из Inbox')),
          );
        },
      ),
    );
  }

  void _showGoalSheet(BuildContext context, WidgetRef ref, InboxItem item) {
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      builder: (_) => GoalCaptureSheet(
        initialTitle: item.title,
        initialDescription: item.note,
        onSubmit: (draft) {
          ref.read(inboxControllerProvider.notifier).saveGoal(draft);
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Цель сохранена из Inbox')),
          );
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(inboxControllerProvider);
    final controller = ref.read(inboxControllerProvider.notifier);
    final currentItem = state.currentItem;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Inbox'),
        actions: <Widget>[
          IconButton(
            tooltip: 'Обновить',
            onPressed: controller.refresh,
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: state.isLoading
            ? const Center(child: CircularProgressIndicator())
            : currentItem == null
                ? _EmptyInbox(
                    processed: state.processedCount,
                    goals: state.convertedGoals.length,
                    onRefresh: controller.refresh,
                  )
                : Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: <Widget>[
                      _InboxProgress(
                        currentIndex: state.currentIndex,
                        total: state.items.length,
                        processed: state.processedCount,
                      ),
                      const SizedBox(height: 12),
                      _InboxItemCard(item: currentItem),
                      const SizedBox(height: 16),
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: <Widget>[
                          FilledButton.icon(
                            onPressed: () => _showTaskSheet(context, ref, currentItem),
                            icon: const Icon(Icons.checklist_rtl),
                            label: const Text('В задачу'),
                          ),
                          OutlinedButton.icon(
                            onPressed: () => _showEventSheet(context, ref, currentItem),
                            icon: const Icon(Icons.event_available_outlined),
                            label: const Text('В событие'),
                          ),
                          OutlinedButton.icon(
                            onPressed: () => _showGoalSheet(context, ref, currentItem),
                            icon: const Icon(Icons.flag_outlined),
                            label: const Text('В цель'),
                          ),
                          TextButton.icon(
                            onPressed: controller.skipCurrent,
                            icon: const Icon(Icons.snooze),
                            label: const Text('Позже'),
                          ),
                          TextButton.icon(
                            onPressed: controller.completeCurrent,
                            icon: const Icon(Icons.archive_outlined),
                            label: const Text('Готово без конверсии'),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      if (state.convertedGoals.isNotEmpty)
                        _GoalSummary(goals: state.convertedGoals),
                    ],
                  ),
      ),
    );
  }
}

class _InboxProgress extends StatelessWidget {
  const _InboxProgress({
    required this.currentIndex,
    required this.total,
    required this.processed,
  });

  final int currentIndex;
  final int total;
  final int processed;

  @override
  Widget build(BuildContext context) {
    final currentStep = currentIndex + 1;
    final value = total == 0 ? 0.0 : currentStep / total;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text(
              'Мастер обработки',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 8),
            LinearProgressIndicator(value: value),
            const SizedBox(height: 8),
            Row(
              children: <Widget>[
                Text('Шаг $currentStep из $total'),
                const Spacer(),
                Row(
                  children: <Widget>[
                    const Icon(Icons.done_all, size: 18),
                    const SizedBox(width: 4),
                    Text('Обработано: $processed'),
                  ],
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _InboxItemCard extends StatelessWidget {
  const _InboxItemCard({required this.item});

  final InboxItem item;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Row(
              children: <Widget>[
                const CircleAvatar(child: Icon(Icons.inbox_outlined)),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      Text(
                        item.title,
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'Захвачено ${_formatDateTime(item.capturedAt)}',
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ],
                  ),
                ),
              ],
            ),
            if (item.note != null && item.note!.isNotEmpty) ...<Widget>[
              const SizedBox(height: 12),
              DecoratedBox(
                decoration: BoxDecoration(
                  color: Theme.of(context).colorScheme.surfaceVariant,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Text(item.note!),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _GoalSummary extends StatelessWidget {
  const _GoalSummary({required this.goals});

  final List<InboxGoal> goals;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Row(
              children: <Widget>[
                const Icon(Icons.flag_circle_outlined),
                const SizedBox(width: 8),
                Text(
                  'Цели из Inbox (${goals.length})',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
              ],
            ),
            const SizedBox(height: 8),
            ...goals.map((goal) => Padding(
                  padding: const EdgeInsets.symmetric(vertical: 4),
                  child: Row(
                    children: <Widget>[
                      const Icon(Icons.check, size: 16),
                      const SizedBox(width: 8),
                      Expanded(child: Text(goal.title)),
                    ],
                  ),
                )),
          ],
        ),
      ),
    );
  }
}

class _EmptyInbox extends StatelessWidget {
  const _EmptyInbox({
    required this.processed,
    required this.goals,
    required this.onRefresh,
  });

  final int processed;
  final int goals;
  final VoidCallback onRefresh;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          const Icon(Icons.inbox_outlined, size: 64),
          const SizedBox(height: 12),
          Text(
            'Все входящие обработаны',
            style: Theme.of(context).textTheme.titleLarge,
          ),
          const SizedBox(height: 8),
          Text('Создано задач: $processed, целей: $goals'),
          const SizedBox(height: 12),
          OutlinedButton.icon(
            onPressed: onRefresh,
            icon: const Icon(Icons.refresh),
            label: const Text('Загрузить заново'),
          ),
        ],
      ),
    );
  }
}

String _formatDateTime(DateTime dateTime) {
  final now = DateTime.now();
  final difference = now.difference(dateTime);
  if (difference.inMinutes < 60) {
    return '${difference.inMinutes} минут назад';
  }
  if (difference.inHours < 24) {
    return '${difference.inHours} часов назад';
  }
  return '${difference.inDays} дн. назад';
}
