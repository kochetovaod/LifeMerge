import '../../../domain/entities/calendar/calendar_event.dart';

enum CalendarOperationType { create, update, delete }

class PendingCalendarOperation {
  PendingCalendarOperation({
    required this.type,
    required this.event,
    required this.requestId,
    required this.enqueuedAt,
  });

  final CalendarOperationType type;
  final CalendarEvent event;
  final String requestId;
  final DateTime enqueuedAt;
}

class CalendarState {
  const CalendarState({
    this.events = const <CalendarEvent>[],
    this.pendingOperations = const <PendingCalendarOperation>[],
    this.isLoading = false,
    this.isOffline = false,
    this.errorMessage,
  });

  final List<CalendarEvent> events;
  final List<PendingCalendarOperation> pendingOperations;
  final bool isLoading;
  final bool isOffline;
  final String? errorMessage;

  CalendarState copyWith({
    List<CalendarEvent>? events,
    List<PendingCalendarOperation>? pendingOperations,
    bool? isLoading,
    bool? isOffline,
    String? errorMessage,
    bool clearError = false,
  }) {
    return CalendarState(
      events: events ?? this.events,
      pendingOperations: pendingOperations ?? this.pendingOperations,
      isLoading: isLoading ?? this.isLoading,
      isOffline: isOffline ?? this.isOffline,
      errorMessage: clearError ? null : errorMessage,
    );
  }
}
