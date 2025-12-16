import '../entities/calendar/calendar_event.dart';

abstract class CalendarRepository {
  Future<List<CalendarEvent>> fetchEvents();
  Future<CalendarEvent> createEvent(CalendarEvent event);
  Future<CalendarEvent> updateEvent(CalendarEvent event);
  Future<void> deleteEvent(String id);
}
