import 'package:flutter/material.dart';

import '../../../domain/entities/calendar/calendar_event.dart';

class EventFormSheet extends StatefulWidget {
  const EventFormSheet({
    super.key,
    this.initialEvent,
    this.initialStartAt,
    this.initialEndAt,
    this.initialTaskId,
    this.initialTaskTitle,
    this.initialTitle,
    required this.onSubmit,
  });

  final CalendarEvent? initialEvent;
  final DateTime? initialStartAt;
  final DateTime? initialEndAt;
  final String? initialTaskId;
  final String? initialTaskTitle;
  final String? initialTitle;
  final void Function(CalendarEventDraft) onSubmit;

  @override
  State<EventFormSheet> createState() => _EventFormSheetState();
}

class _EventFormSheetState extends State<EventFormSheet> {
  late final TextEditingController _titleController;
  late final TextEditingController _descriptionController;
  late DateTime _startAt;
  DateTime? _endAt;
  String? _taskId;
  String? _taskTitle;
  final GlobalKey<FormState> _formKey = GlobalKey<FormState>();

  @override
  void initState() {
    super.initState();
    _titleController =
        TextEditingController(text: widget.initialEvent?.title ?? widget.initialTitle ?? '');
    _descriptionController =
        TextEditingController(text: widget.initialEvent?.description ?? '');
    _startAt =
        widget.initialEvent?.startAt ?? widget.initialStartAt ?? DateTime.now();
    _endAt = widget.initialEvent?.endAt ?? widget.initialEndAt;
    _taskId = widget.initialEvent?.taskId ?? widget.initialTaskId;
    _taskTitle = widget.initialTaskTitle;
  }

  @override
  void dispose() {
    _titleController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  Future<void> _pickStartDateTime() async {
    final pickedDate = await showDatePicker(
      context: context,
      initialDate: _startAt,
      firstDate: DateTime.now().subtract(const Duration(days: 365)),
      lastDate: DateTime.now().add(const Duration(days: 365)),
    );
    if (pickedDate == null) return;

    final pickedTime = await showTimePicker(
      context: context,
      initialTime: TimeOfDay.fromDateTime(_startAt),
    );
    if (pickedTime == null) return;

    setState(() {
      _startAt = DateTime(
        pickedDate.year,
        pickedDate.month,
        pickedDate.day,
        pickedTime.hour,
        pickedTime.minute,
      );
    });
  }

  Future<void> _pickEndDateTime() async {
    final pickedDate = await showDatePicker(
      context: context,
      initialDate: _endAt ?? _startAt,
      firstDate: _startAt,
      lastDate: _startAt.add(const Duration(days: 2)),
    );
    if (pickedDate == null) return;

    final pickedTime = await showTimePicker(
      context: context,
      initialTime: TimeOfDay.fromDateTime(_endAt ?? _startAt.add(const Duration(hours: 1))),
    );
    if (pickedTime == null) return;

    setState(() {
      _endAt = DateTime(
        pickedDate.year,
        pickedDate.month,
        pickedDate.day,
        pickedTime.hour,
        pickedTime.minute,
      );
    });
  }

  void _submit() {
    if (!_formKey.currentState!.validate()) {
      return;
    }
    final draft = CalendarEventDraft(
      title: _titleController.text.trim(),
      startAt: _startAt,
      endAt: _endAt,
      description: _descriptionController.text.trim().isEmpty
          ? null
          : _descriptionController.text.trim(),
      taskId: _taskId,
    );
    widget.onSubmit(draft);
    Navigator.of(context).pop();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: EdgeInsets.only(
        left: 16,
        right: 16,
        bottom: MediaQuery.of(context).viewInsets.bottom + 16,
        top: 16,
      ),
      child: Form(
        key: _formKey,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            Text(
              widget.initialEvent == null ? 'New event' : 'Edit event',
              style: theme.textTheme.titleLarge,
            ),
            const SizedBox(height: 12),
            if (_taskId != null)
              Container(
                width: double.infinity,
                margin: const EdgeInsets.only(bottom: 12),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: theme.colorScheme.secondaryContainer,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    const Icon(Icons.link, size: 20),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Linked task',
                            style: theme.textTheme.labelLarge,
                          ),
                          const SizedBox(height: 4),
                          Text(
                            _taskTitle ?? _taskId!,
                            style: theme.textTheme.bodyMedium,
                          ),
                        ],
                      ),
                    ),
                    IconButton(
                      onPressed: () => setState(() => _taskId = null),
                      tooltip: 'Remove link',
                      icon: const Icon(Icons.close),
                    ),
                  ],
                ),
              ),
            TextFormField(
              controller: _titleController,
              decoration: const InputDecoration(labelText: 'Title'),
              validator: (value) {
                if (value == null || value.trim().isEmpty) {
                  return 'Required';
                }
                return null;
              },
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: _descriptionController,
              decoration: const InputDecoration(labelText: 'Description (optional)'),
              minLines: 1,
              maxLines: 3,
            ),
            const SizedBox(height: 12),
            ListTile(
              leading: const Icon(Icons.schedule),
              title: const Text('Start'),
              subtitle: Text('${_startAt.toLocal()}'),
              onTap: _pickStartDateTime,
            ),
            ListTile(
              leading: const Icon(Icons.event_available),
              title: const Text('End (optional)'),
              subtitle: Text(_endAt != null ? '${_endAt!.toLocal()}' : 'Not set'),
              onTap: _pickEndDateTime,
            ),
            const SizedBox(height: 8),
            Align(
              alignment: Alignment.centerRight,
              child: FilledButton.icon(
                icon: const Icon(Icons.save_outlined),
                label: Text(widget.initialEvent == null ? 'Save event' : 'Update event'),
                onPressed: _submit,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
