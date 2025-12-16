import '../entities/inbox/inbox_goal.dart';
import '../entities/inbox/inbox_item.dart';

abstract class InboxRepository {
  Future<List<InboxItem>> fetchItems();
  Future<void> removeItem(String id);
  Future<void> moveToEnd(String id);
  Future<InboxGoal> saveGoal(GoalDraft draft, InboxItem source);
}
