import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../domain/calendar_event.dart';
import 'calendar_api_service.dart';

class CalendarRepository {
  CalendarRepository(this._apiService);

  final CalendarApiService _apiService;

  Future<List<CalendarEvent>> fetchEvents() => _apiService.fetchEvents();

  Future<CalendarEvent> createEvent(CalendarEvent event) => _apiService.createEvent(event);

  Future<CalendarEvent> updateEvent(CalendarEvent event) => _apiService.updateEvent(event);

  Future<void> deleteEvent(String id) => _apiService.deleteEvent(id);
}

final calendarApiServiceProvider = Provider<CalendarApiService>((ref) {
  return CalendarApiService();
});

final calendarRepositoryProvider = Provider<CalendarRepository>((ref) {
  final api = ref.read(calendarApiServiceProvider);
  return CalendarRepository(api);
});
