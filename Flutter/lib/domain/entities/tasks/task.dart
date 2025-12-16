import 'package:meta/meta.dart';

enum TaskStatus { todo, inProgress, done, deferred }

enum TaskPriority { low, medium, high }

@immutable
class Task {
  const Task({
    required this.id,
    required this.title,
    this.description,
    this.dueAt,
    this.priority = TaskPriority.medium,
    this.estimatedMinutes,
    this.energyLevel,
    this.status = TaskStatus.todo,
    required this.createdAt,
    required this.updatedAt,
    this.deleted = false,
  });

  final String id;
  final String title;
  final String? description;
  final DateTime? dueAt;
  final TaskPriority priority;
  final int? estimatedMinutes;
  final String? energyLevel;
  final TaskStatus status;
  final DateTime createdAt;
  final DateTime updatedAt;
  final bool deleted;

  Task copyWith({
    String? id,
    String? title,
    String? description,
    DateTime? dueAt,
    TaskPriority? priority,
    int? estimatedMinutes,
    String? energyLevel,
    TaskStatus? status,
    DateTime? createdAt,
    DateTime? updatedAt,
    bool? deleted,
  }) {
    return Task(
      id: id ?? this.id,
      title: title ?? this.title,
      description: description ?? this.description,
      dueAt: dueAt ?? this.dueAt,
      priority: priority ?? this.priority,
      estimatedMinutes: estimatedMinutes ?? this.estimatedMinutes,
      energyLevel: energyLevel ?? this.energyLevel,
      status: status ?? this.status,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      deleted: deleted ?? this.deleted,
    );
  }

  factory Task.fromJson(Map<String, dynamic> json) {
    return Task(
      id: json['id'] as String,
      title: json['title'] as String,
      description: json['description'] as String?,
      dueAt: json['due_at'] != null ? DateTime.parse(json['due_at'] as String) : null,
      priority: _priorityFromJson(json['priority']),
      estimatedMinutes: json['estimated_minutes'] as int?,
      energyLevel: json['energy_level'] as String?,
      status: _statusFromJson(json['status']),
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
      deleted: json['deleted'] as bool? ?? false,
    );
  }

  Map<String, dynamic> toJson() {
    return <String, dynamic>{
      'id': id,
      'title': title,
      'description': description,
      'due_at': dueAt?.toIso8601String(),
      'priority': priority.name,
      'estimated_minutes': estimatedMinutes,
      'energy_level': energyLevel,
      'status': status.name,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
      'deleted': deleted,
    };
  }
}

class TaskDraft {
  const TaskDraft({
    required this.title,
    this.description,
    this.dueAt,
    this.priority = TaskPriority.medium,
    this.estimatedMinutes,
    this.energyLevel,
    this.status = TaskStatus.todo,
  });

  final String title;
  final String? description;
  final DateTime? dueAt;
  final TaskPriority priority;
  final int? estimatedMinutes;
  final String? energyLevel;
  final TaskStatus status;

  Map<String, dynamic> toJson() {
    return <String, dynamic>{
      'title': title,
      'description': description,
      'due_at': dueAt?.toIso8601String(),
      'priority': priority.name,
      'estimated_minutes': estimatedMinutes,
      'energy_level': energyLevel,
      'status': status.name,
    };
  }
}

TaskPriority _priorityFromJson(dynamic raw) {
  if (raw is String) {
    return TaskPriority.values.firstWhere(
      (priority) => priority.name == raw,
      orElse: () => TaskPriority.medium,
    );
  }
  return TaskPriority.medium;
}

TaskStatus _statusFromJson(dynamic raw) {
  if (raw is String) {
    return TaskStatus.values.firstWhere(
      (status) => status.name == raw,
      orElse: () => TaskStatus.todo,
    );
  }
  return TaskStatus.todo;
}
