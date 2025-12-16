import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

import '../../../domain/entities/tasks/task.dart';

class TasksCache {
  TasksCache(this._prefs);

  final SharedPreferences _prefs;

  static const _key = 'tasks_cache_v1';

  List<Task> read() {
    final raw = _prefs.getString(_key);
    if (raw == null) return <Task>[];
    try {
      final list = (json.decode(raw) as List).cast<Map<String, dynamic>>();
      return list.map(Task.fromJson).toList();
    } catch (_) {
      return <Task>[];
    }
  }

  Future<void> write(List<Task> tasks) async {
    final raw = json.encode(tasks.map((e) => e.toJson()).toList());
    await _prefs.setString(_key, raw);
  }

  Future<void> clear() => _prefs.remove(_key);
}
