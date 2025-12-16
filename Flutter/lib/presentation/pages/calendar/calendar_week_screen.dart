import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../app/router/routes.dart';
import '../../../domain/entities/calendar/calendar_event.dart';
import '../../blocs/calendar/calendar_controller.dart';
import '../../providers/presentation_providers.dart';

class CalendarWeekScreen extends ConsumerWidget {
  const CalendarWeekScreen({super.key});

  Map<int, List<CalendarEvent>> _groupByWeekday(List<CalendarEvent> events) {
    final map = <int, List<CalendarEvent>>{};
    for (final event in events.where((e) => !e.deleted)) {
      final key = event.startAt.weekday;
      map.putIfAbsent(key, () => <CalendarEvent>[]).add(event);
    }
    map.updateAll((_, list) {
      list.sort((a, b) => a.startAt.compareTo(b.startAt));
      return list;
    });
    return map;
  }

  Iterable<CalendarEvent> _overlaps(List<CalendarEvent> events) sync* {
    for (var i = 0; i < events.length - 1; i++) {
      final current = events[i];
      final next = events[i + 1];
      if (current.endAt.isAfter(next.startAt)) {
        yield current;
        yield next;
      }
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(calendarControllerProvider);
    final grouped = _groupByWeekday(state.events);
    final today = DateTime.now();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Календарь · Неделя'),
        actions: <Widget>[
          IconButton(
            icon: const Icon(Icons.view_day_outlined),
            tooltip: 'День',
            onPressed: () => context.go(Routes.calendarDay),
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: ref.read(calendarControllerProvider.notifier).refresh,
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: <Widget>[
          Wrap(
            spacing: 12,
            runSpacing: 8,
            children: <Widget>[
              Chip(
                avatar: const Icon(Icons.directions_walk, size: 18),
                label: const Text('Буферы на дорогу 15 мин между встречами'),
              ),
              Chip(
                avatar: const Icon(Icons.warning_amber, size: 18),
                label: Text('Пересечений: ${state.events.length - state.events.toSet().length}'),
              ),
              Chip(
                avatar: const Icon(Icons.nightlight_round, size: 18),
                label: Text('Смены: ${(grouped.length)} дней из 7 заполнены'),
              ),
            ],
          ),
          const SizedBox(height: 12),
          GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 2,
              mainAxisSpacing: 12,
              crossAxisSpacing: 12,
              childAspectRatio: 1.1,
            ),
            itemCount: 7,
            itemBuilder: (context, index) {
              final weekday = index + 1;
              final isToday = weekday == today.weekday;
              final dayEvents = grouped[weekday] ?? <CalendarEvent>[];
              final conflicts = _overlaps(dayEvents).toSet();
              return Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Theme.of(context).dividerColor),
                  color: isToday ? Theme.of(context).colorScheme.primary.withOpacity(0.05) : null,
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Row(
                      children: <Widget>[
                        Text('День $weekday', style: Theme.of(context).textTheme.titleMedium),
                        const Spacer(),
                        if (isToday) const Chip(label: Text('Сегодня')),
                      ],
                    ),
                    const SizedBox(height: 6),
                    Expanded(
                      child: ListView.separated(
                        itemCount: dayEvents.length,
                        separatorBuilder: (_, __) => const SizedBox(height: 6),
                        itemBuilder: (context, i) {
                          final event = dayEvents[i];
                          final hasConflict = conflicts.contains(event);
                          return Container(
                            padding: const EdgeInsets.all(10),
                            decoration: BoxDecoration(
                              color: hasConflict
                                  ? Theme.of(context).colorScheme.errorContainer
                                  : Theme.of(context).colorScheme.surfaceVariant,
                              borderRadius: BorderRadius.circular(10),
                            ),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: <Widget>[
                                Text(event.title, style: Theme.of(context).textTheme.titleSmall),
                                Text(
                                  '${TimeOfDay.fromDateTime(event.startAt).format(context)} '
                                  '→ ${TimeOfDay.fromDateTime(event.endAt).format(context)}',
                                  style: Theme.of(context).textTheme.bodySmall,
                                ),
                                if (hasConflict)
                                  Row(
                                    children: const <Widget>[
                                      Icon(Icons.report_problem, size: 16),
                                      SizedBox(width: 4),
                                      Text('Есть пересечение и нужен буфер'),
                                    ],
                                  ),
                                if (event.description != null)
                                  Padding(
                                    padding: const EdgeInsets.only(top: 2),
                                    child: Text(event.description!, maxLines: 2, overflow: TextOverflow.ellipsis),
                                  ),
                              ],
                            ),
                          );
                        },
                      ),
                    ),
                  ],
                ),
              );
            },
          ),
        ],
      ),
    );
  }
}
