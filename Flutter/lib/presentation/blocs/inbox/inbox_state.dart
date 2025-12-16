import 'package:meta/meta.dart';

import '../../../domain/entities/inbox/inbox_goal.dart';
import '../../../domain/entities/inbox/inbox_item.dart';

@immutable
class InboxState {
  const InboxState({
    this.isLoading = false,
    this.errorMessage,
    this.items = const <InboxItem>[],
    this.processedCount = 0,
    this.currentIndex = 0,
    this.convertedGoals = const <InboxGoal>[],
  });

  final bool isLoading;
  final String? errorMessage;
  final List<InboxItem> items;
  final int processedCount;
  final int currentIndex;
  final List<InboxGoal> convertedGoals;

  InboxItem? get currentItem {
    if (items.isEmpty) return null;
    final safeIndex = currentIndex.clamp(0, items.length - 1);
    return items[safeIndex];
  }

  InboxState copyWith({
    bool? isLoading,
    String? errorMessage,
    bool clearError = false,
    List<InboxItem>? items,
    int? processedCount,
    int? currentIndex,
    List<InboxGoal>? convertedGoals,
  }) {
    return InboxState(
      isLoading: isLoading ?? this.isLoading,
      errorMessage: clearError ? null : errorMessage ?? this.errorMessage,
      items: items ?? this.items,
      processedCount: processedCount ?? this.processedCount,
      currentIndex: currentIndex ?? this.currentIndex,
      convertedGoals: convertedGoals ?? this.convertedGoals,
    );
  }
}
