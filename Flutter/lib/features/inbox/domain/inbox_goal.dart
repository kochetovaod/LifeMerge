import 'package:flutter/foundation.dart';

@immutable
class InboxGoal {
  const InboxGoal({
    required this.id,
    required this.title,
    this.description,
    required this.sourceItemId,
    required this.createdAt,
  });

  final String id;
  final String title;
  final String? description;
  final String sourceItemId;
  final DateTime createdAt;
}

@immutable
class GoalDraft {
  const GoalDraft({
    required this.title,
    this.description,
  });

  final String title;
  final String? description;
}
