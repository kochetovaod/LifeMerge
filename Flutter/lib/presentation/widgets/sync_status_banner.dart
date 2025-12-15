import 'package:flutter/material.dart';

class SyncQueueItem {
  const SyncQueueItem({
    required this.id,
    required this.title,
    required this.description,
    required this.enqueuedAt,
    required this.typeLabel,
    this.isConflict = false,
  });

  final String id;
  final String title;
  final String description;
  final DateTime enqueuedAt;
  final String typeLabel;
  final bool isConflict;
}

class SyncStatusBanner extends StatelessWidget {
  const SyncStatusBanner({
    super.key,
    required this.isOffline,
    required this.queueItems,
    required this.onSyncNow,
    this.errorMessage,
    this.onDismissError,
    this.title,
  });

  final bool isOffline;
  final List<SyncQueueItem> queueItems;
  final VoidCallback onSyncNow;
  final String? errorMessage;
  final VoidCallback? onDismissError;
  final String? title;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final hasQueue = queueItems.isNotEmpty;
    final hasError = errorMessage != null;

    if (!isOffline && !hasQueue && !hasError) {
      return const SizedBox.shrink();
    }

    return Card(
      margin: const EdgeInsets.fromLTRB(12, 8, 12, 4),
      color: isOffline
          ? theme.colorScheme.surfaceVariant
          : theme.colorScheme.surface,
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  hasError
                      ? Icons.sync_problem
                      : (isOffline ? Icons.cloud_off : Icons.cloud_queue),
                  color: hasError
                      ? theme.colorScheme.error
                      : theme.colorScheme.primary,
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        title ?? 'Offline mode',
                        style: theme.textTheme.titleMedium,
                      ),
                      const SizedBox(height: 4),
                      Text(
                        _statusMessage(hasQueue),
                        style: theme.textTheme.bodyMedium,
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 8),
                FilledButton.icon(
                  onPressed: isOffline ? null : onSyncNow,
                  icon: const Icon(Icons.sync),
                  label: const Text('Sync now'),
                ),
              ],
            ),
            if (hasError) ...[
              const SizedBox(height: 12),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: theme.colorScheme.error.withOpacity(0.08),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: theme.colorScheme.error),
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Icon(Icons.error_outline),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            errorMessage!,
                            style: theme.textTheme.bodyMedium,
                          ),
                          const SizedBox(height: 4),
                          Text(
                            'Resolve conflicts, then retry sync. You can keep working offline.',
                            style: theme.textTheme.labelMedium,
                          ),
                        ],
                      ),
                    ),
                    if (onDismissError != null)
                      IconButton(
                        tooltip: 'Dismiss',
                        onPressed: onDismissError,
                        icon: const Icon(Icons.close),
                      ),
                  ],
                ),
              ),
            ],
            if (hasQueue) ...[
              const SizedBox(height: 10),
              _QueueList(queueItems: queueItems),
            ],
          ],
        ),
      ),
    );
  }

  String _statusMessage(bool hasQueue) {
    if (errorMessage != null) {
      return 'Sync paused: tap "Sync now" after resolving issues.';
    }
    if (isOffline && hasQueue) {
      return 'You are offline. ${queueItems.length} change(s) will sync once back online.';
    }
    if (isOffline) {
      return 'You are offline. New changes stay on this device until you reconnect.';
    }
    if (hasQueue) {
      return '${queueItems.length} queued change(s) waiting to sync.';
    }
    return 'Up to date.';
  }
}

class _QueueList extends StatelessWidget {
  const _QueueList({required this.queueItems});

  final List<SyncQueueItem> queueItems;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return ExpansionTile(
      title: Text('Queued changes (${queueItems.length})'),
      subtitle: const Text('Review offline actions and conflicts'),
      children: queueItems
          .map(
            (item) => ListTile(
              leading: Icon(
                item.isConflict ? Icons.priority_high : Icons.pending_actions,
                color: item.isConflict
                    ? theme.colorScheme.error
                    : theme.colorScheme.primary,
              ),
              title: Text(item.title),
              subtitle: Text('${item.typeLabel} • ${item.description}'),
              trailing: Text(
                _timeLabel(item.enqueuedAt),
                style: theme.textTheme.labelMedium,
              ),
            ),
          )
          .toList(),
    );
  }

  String _timeLabel(DateTime value) {
    final hour = value.hour.toString().padLeft(2, '0');
    final minute = value.minute.toString().padLeft(2, '0');
    return '$hour:$minute';
  }
}
