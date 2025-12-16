import 'package:dio/dio.dart';

class ApiClient {
  ApiClient(this._dio);

  final Dio _dio;

  Future<Map<String, dynamic>> signup(Map<String, dynamic> data) async {
    final response = await _dio.post('/auth/signup', data: data);
    return response.data;
  }

  Future<Map<String, dynamic>> login(Map<String, dynamic> data) async {
    final response = await _dio.post('/auth/login', data: data);
    return response.data;
  }

  Future<Map<String, dynamic>> refreshToken(Map<String, dynamic> data) async {
    final response = await _dio.post('/auth/refresh', data: data);
    return response.data;
  }

  Future<Map<String, dynamic>> logout(Map<String, dynamic> data) async {
    final response = await _dio.post('/auth/logout', data: data);
    return response.data;
  }

  Future<Map<String, dynamic>> getTasks({
    String? status,
    String? goalId,
    DateTime? dueFrom,
    DateTime? dueTo,
    String? cursor,
    int limit = 50,
  }) async {
    final response = await _dio.get('/tasks', queryParameters: <String, dynamic>{
      if (status != null) 'status': status,
      if (goalId != null) 'goal_id': goalId,
      if (dueFrom != null) 'due_from': dueFrom.toIso8601String(),
      if (dueTo != null) 'due_to': dueTo.toIso8601String(),
      if (cursor != null) 'cursor': cursor,
      'limit': limit,
    });
    return response.data;
  }

  Future<Map<String, dynamic>> createTask(Map<String, dynamic> data) async {
    final response = await _dio.post('/tasks', data: data);
    return response.data;
  }

  Future<Map<String, dynamic>> updateTask(String taskId, Map<String, dynamic> data) async {
    final response = await _dio.patch('/tasks/$taskId', data: data);
    return response.data;
  }

  Future<Map<String, dynamic>> deleteTask(String taskId, Map<String, dynamic> data) async {
    final response = await _dio.delete('/tasks/$taskId', data: data);
    return response.data;
  }
}
