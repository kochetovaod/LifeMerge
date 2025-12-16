// lib/core/sync/sync_service.dart
import 'package:hive/hive.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import '../../data/datasources/remote/api_client.dart';
import '../../domain/entities/tasks/task.dart';

class SyncService {
  final ApiClient _apiClient;
  final Box<SyncOperation> _syncQueueBox;

  SyncService(this._apiClient)
      : _syncQueueBox = Hive.box<SyncOperation>('sync_queue');

  Future<void> syncAll() async {
    final connectivityResult = await Connectivity().checkConnectivity();
    if (connectivityResult == ConnectivityResult.none) {
      return;
    }

    final pendingOperations = _syncQueueBox.values.toList();
    
    for (final operation in pendingOperations) {
      try {
        await _processOperation(operation);
        await _syncQueueBox.delete(operation.id);
      } catch (e) {
        // Увеличиваем счетчик попыток
        await _syncQueueBox.put(
          operation.id,
          operation.copyWith(
            attempts: operation.attempts + 1,
            lastError: e.toString(),
          ),
        );
      }
    }
  }

  Future<void> queueOperation(SyncOperation operation) async {
    await _syncQueueBox.put(operation.id, operation);
    
    // Попробуем синхронизировать сразу
    final connectivityResult = await Connectivity().checkConnectivity();
    if (connectivityResult != ConnectivityResult.none) {
      await syncAll();
    }
  }

  Future<void> _processOperation(SyncOperation operation) async {
    switch (operation.type) {
      case 'task_create':
        await _apiClient.createTask(operation.data);
        break;
      case 'task_update':
        await _apiClient.updateTask(operation.entityId, operation.data);
        break;
      case 'task_delete':
        await _apiClient.deleteTask(operation.entityId, operation.data);
        break;
    }
  }
}

@HiveType(typeId: 2)
class SyncOperation {
  @HiveField(0)
  final String id;
  
  @HiveField(1)
  final String type; // task_create, task_update, task_delete
  
  @HiveField(2)
  final String entityId;
  
  @HiveField(3)
  final Map<String, dynamic> data;
  
  @HiveField(4)
  final DateTime createdAt;
  
  @HiveField(5)
  int attempts;
  
  @HiveField(6)
  String? lastError;

  SyncOperation({
    required this.id,
    required this.type,
    required this.entityId,
    required this.data,
    required this.createdAt,
    this.attempts = 0,
    this.lastError,
  });

  SyncOperation copyWith({
    int? attempts,
    String? lastError,
  }) {
    return SyncOperation(
      id: id,
      type: type,
      entityId: entityId,
      data: data,
      createdAt: createdAt,
      attempts: attempts ?? this.attempts,
      lastError: lastError ?? this.lastError,
    );
  }
}