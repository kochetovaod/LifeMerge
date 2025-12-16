import '../../domain/entities/calendar/calendar_event.dart';
import '../../domain/repositories/calendar_repository.dart';
import '../datasources/remote/calendar_api_service.dart';

class CalendarRepositoryImpl implements CalendarRepository {
  CalendarRepositoryImpl(this._apiService);

  final CalendarApiService _apiService;

  @override
  Future<List<CalendarEvent>> fetchEvents() => _apiService.fetchEvents();

  @override
  Future<CalendarEvent> createEvent(CalendarEvent event) => _apiService.createEvent(event);

  @override
  Future<CalendarEvent> updateEvent(CalendarEvent event) => _apiService.updateEvent(event);

  @override
  Future<void> deleteEvent(String id) => _apiService.deleteEvent(id);
}
