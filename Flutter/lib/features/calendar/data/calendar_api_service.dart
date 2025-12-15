import 'dart:async';

import '../domain/calendar_event.dart';

class CalendarApiService {
  CalendarApiService() {
    final now = DateTime.now();
    _remoteEvents.addAll(<CalendarEvent>[
      CalendarEvent(
        id: _generateId(),
        title: 'Product sync',
        startAt: DateTime(now.year, now.month, now.day, 10, 0),
        endAt: DateTime(now.year, now.month, now.day, 11, 0),
        description: 'Weekly priorities review',
        createdAt: now.subtract(const Duration(days: 1)),
        updatedAt: now.subtract(const Duration(days: 1)),
      ),
      CalendarEvent(
        id: _generateId(),
        title: 'Coffee with Alex',
        startAt: DateTime(now.year, now.month, now.day, 15, 0),
        endAt: DateTime(now.year, now.month, now.day, 15, 30),
        description: 'Catch up on side project',
        createdAt: now.subtract(const Duration(hours: 2)),
        updatedAt: now.subtract(const Duration(hours: 2)),
      ),
    ]);
  }

  final List<CalendarEvent> _remoteEvents = <CalendarEvent>[];

  Future<List<CalendarEvent>> fetchEvents() async {
    await Future<void>.delayed(const Duration(milliseconds: 500));
    return List<CalendarEvent>.unmodifiable(_remoteEvents.where((event) => !event.deleted));
  }

  Future<CalendarEvent> createEvent(CalendarEvent event) async {
    await Future<void>.delayed(const Duration(milliseconds: 400));
    final now = DateTime.now();
    final created = event.copyWith(
      id: event.id.isEmpty || event.id.startsWith('local') ? _generateId() : event.id,
      createdAt: event.createdAt == event.updatedAt ? now : event.createdAt,
      updatedAt: now,
      taskId: event.taskId,
      deleted: false,
    );
    _remoteEvents.removeWhere((existing) => existing.id == created.id);
    _remoteEvents.add(created);
    return created;
  }

  Future<CalendarEvent> updateEvent(CalendarEvent event) async {
    await Future<void>.delayed(const Duration(milliseconds: 400));
    final current = _remoteEvents.firstWhere((item) => item.id == event.id, orElse: () => event);
    final updated = current.copyWith(
      title: event.title,
      description: event.description,
      startAt: event.startAt,
      endAt: event.endAt,
      taskId: event.taskId,
      status: event.status,
      updatedAt: DateTime.now(),
    );
    _remoteEvents.removeWhere((existing) => existing.id == updated.id);
    _remoteEvents.add(updated);
    return updated;
  }

  Future<void> deleteEvent(String id) async {
    await Future<void>.delayed(const Duration(milliseconds: 300));
    final currentIndex = _remoteEvents.indexWhere((event) => event.id == id);
    if (currentIndex != -1) {
      final current = _remoteEvents[currentIndex];
      _remoteEvents[currentIndex] = current.copyWith(
        deleted: true,
        updatedAt: DateTime.now(),
      );
    }
  }

  String _generateId() => DateTime.now().microsecondsSinceEpoch.toString();
}
