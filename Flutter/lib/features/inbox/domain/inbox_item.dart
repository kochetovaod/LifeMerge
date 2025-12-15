import 'package:flutter/foundation.dart';

@immutable
class InboxItem {
  const InboxItem({
    required this.id,
    required this.title,
    this.note,
    required this.capturedAt,
  });

  final String id;
  final String title;
  final String? note;
  final DateTime capturedAt;
}
