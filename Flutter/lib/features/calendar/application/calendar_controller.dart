import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/calendar_repository.dart';
import '../domain/calendar_event.dart';
import 'calendar_state.dart';

class CalendarController extends StateNotifier<CalendarState> {
  CalendarController(this._repository) : super(const CalendarState()) {
    _loadEvents();
  }

  final CalendarRepository _repository;
  Timer? _retryTimer;

  Future<void> _loadEvents() async {
    state = state.copyWith(isLoading: true, clearError: true);
    await _flushQueue(force: true);
    try {
      final events = await _repository.fetchEvents();
      state = state.copyWith(events: events, isLoading: false, clearError: true);
    } catch (error) {
      state = state.copyWith(
        isLoading: false,
        errorMessage: error.toString(),
      );
    }
  }

  Future<void> refresh() => _loadEvents();

  Future<void> syncPending() => _flushQueue(force: true);

  Future<void> addEvent(CalendarEventDraft draft) async {
    final now = DateTime.now();
    final pending = CalendarEvent(
      id: _generateRequestId(prefix: 'local'),
      title: draft.title,
      description: draft.description,
      startAt: draft.startAt,
      endAt: draft.endAt,
      taskId: draft.taskId,
      status: CalendarEventStatus.scheduled,
      createdAt: now,
      updatedAt: now,
    );

    if (state.isOffline) {
      _enqueueOperation(CalendarOperationType.create, pending);
      _applyLocalChange(pending);
      return;
    }

    await _executeCreate(pending);
  }

  Future<void> updateEvent(CalendarEvent event, CalendarEventDraft draft) async {
    final updated = event.copyWith(
      title: draft.title,
      description: draft.description,
      startAt: draft.startAt,
      endAt: draft.endAt,
      taskId: draft.taskId ?? event.taskId,
      updatedAt: DateTime.now(),
    );

    if (state.isOffline) {
      _enqueueOperation(CalendarOperationType.update, updated);
      _replaceEvent(event.id, updated);
      return;
    }

    await _executeUpdate(updated);
  }

  Future<void> deleteEvent(CalendarEvent event) async {
    final deleted = event.copyWith(deleted: true, updatedAt: DateTime.now());
    if (state.isOffline) {
      _enqueueOperation(CalendarOperationType.delete, deleted);
      _removeEvent(event.id);
      return;
    }

    await _executeDelete(deleted);
  }

  void toggleOfflineMode() {
    final wasOffline = state.isOffline;
    state = state.copyWith(isOffline: !state.isOffline);
    if (wasOffline && !state.isOffline) {
      unawaited(_flushQueue(force: true));
    }
  }

  void clearError() {
    if (state.errorMessage != null) {
      state = state.copyWith(clearError: true);
    }
  }

  void _applyLocalChange(CalendarEvent event) {
    state = state.copyWith(events: <CalendarEvent>[...state.events, event]);
  }

  void _replaceEvent(String originalId, CalendarEvent updated) {
    final events = state.events.map((event) => event.id == originalId ? updated : event).toList();
    state = state.copyWith(events: events);
  }

  void _removeEvent(String id) {
    state = state.copyWith(events: state.events.where((event) => event.id != id).toList());
  }

  void _enqueueOperation(CalendarOperationType type, CalendarEvent event) {
    final operation = PendingCalendarOperation(
      type: type,
      event: event,
      requestId: _generateRequestId(),
      enqueuedAt: DateTime.now(),
    );
    state = state.copyWith(
      pendingOperations: <PendingCalendarOperation>[...state.pendingOperations, operation],
    );
    _scheduleRetry();
  }

  Future<void> _flushQueue({bool force = false}) async {
    if (state.pendingOperations.isEmpty) {
      _cancelRetry();
      return;
    }

    if (state.isOffline && !force) {
      _scheduleRetry();
      return;
    }

    final List<PendingCalendarOperation> remaining = <PendingCalendarOperation>[];
    var hadError = false;

    for (final operation in state.pendingOperations) {
      try {
        switch (operation.type) {
          case CalendarOperationType.create:
            final created = await _repository.createEvent(operation.event);
            _replaceEvent(operation.event.id, created);
            break;
          case CalendarOperationType.update:
            final updated = await _repository.updateEvent(operation.event);
            _replaceEvent(operation.event.id, updated);
            break;
          case CalendarOperationType.delete:
            await _repository.deleteEvent(operation.event.id);
            _removeEvent(operation.event.id);
            break;
        }
      } catch (error) {
        hadError = true;
        remaining.add(operation);
      }
    }

    state = state.copyWith(
      pendingOperations: remaining,
      isOffline: hadError && remaining.isNotEmpty,
    );

    if (remaining.isEmpty) {
      _cancelRetry();
    } else {
      _scheduleRetry();
    }
  }

  Future<void> _executeCreate(CalendarEvent event) async {
    try {
      final created = await _repository.createEvent(event);
      _applyOrInsert(created);
    } catch (error) {
      _enqueueOperation(CalendarOperationType.create, event);
      state = state.copyWith(errorMessage: error.toString(), isOffline: true);
    }
  }

  Future<void> _executeUpdate(CalendarEvent event) async {
    try {
      final updated = await _repository.updateEvent(event);
      _replaceEvent(event.id, updated);
    } catch (error) {
      _enqueueOperation(CalendarOperationType.update, event);
      state = state.copyWith(errorMessage: error.toString(), isOffline: true);
    }
  }

  Future<void> _executeDelete(CalendarEvent event) async {
    try {
      await _repository.deleteEvent(event.id);
      _removeEvent(event.id);
    } catch (error) {
      _enqueueOperation(CalendarOperationType.delete, event);
      state = state.copyWith(errorMessage: error.toString(), isOffline: true);
    }
  }

  void _applyOrInsert(CalendarEvent event) {
    final events = [...state.events];
    final index = events.indexWhere((element) => element.id == event.id);
    if (index == -1) {
      events.add(event);
    } else {
      events[index] = event;
    }
    state = state.copyWith(events: events);
  }

  String _generateRequestId({String prefix = 'req'}) {
    final timestamp = DateTime.now().microsecondsSinceEpoch;
    return '$prefix-$timestamp';
  }

  void _scheduleRetry() {
    _retryTimer ??= Timer.periodic(const Duration(seconds: 4), (_) {
      unawaited(_flushQueue(force: true));
    });
  }

  void _cancelRetry() {
    _retryTimer?.cancel();
    _retryTimer = null;
  }
}

final calendarControllerProvider =
    StateNotifierProvider<CalendarController, CalendarState>((ref) {
  final repository = ref.read(calendarRepositoryProvider);
  return CalendarController(repository);
});
