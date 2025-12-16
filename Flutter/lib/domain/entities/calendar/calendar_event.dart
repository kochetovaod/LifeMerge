import 'package:meta/meta.dart';

enum CalendarEventStatus { scheduled, done, canceled }

@immutable
class CalendarEvent {
  const CalendarEvent({
    required this.id,
    required this.title,
    required this.startAt,
    this.endAt,
    this.description,
    this.taskId,
    this.status = CalendarEventStatus.scheduled,
    required this.createdAt,
    required this.updatedAt,
    this.deleted = false,
  });

  final String id;
  final String title;
  final DateTime startAt;
  final DateTime? endAt;
  final String? description;
  final String? taskId;
  final CalendarEventStatus status;
  final DateTime createdAt;
  final DateTime updatedAt;
  final bool deleted;

  CalendarEvent copyWith({
    String? id,
    String? title,
    DateTime? startAt,
    DateTime? endAt,
    String? description,
    String? taskId,
    CalendarEventStatus? status,
    DateTime? createdAt,
    DateTime? updatedAt,
    bool? deleted,
  }) {
    return CalendarEvent(
      id: id ?? this.id,
      title: title ?? this.title,
      startAt: startAt ?? this.startAt,
      endAt: endAt ?? this.endAt,
      description: description ?? this.description,
      taskId: taskId ?? this.taskId,
      status: status ?? this.status,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      deleted: deleted ?? this.deleted,
    );
  }
}

@immutable
class CalendarEventDraft {
  const CalendarEventDraft({
    required this.title,
    required this.startAt,
    this.endAt,
    this.description,
    this.taskId,
  });

  final String title;
  final DateTime startAt;
  final DateTime? endAt;
  final String? description;
  final String? taskId;
}
