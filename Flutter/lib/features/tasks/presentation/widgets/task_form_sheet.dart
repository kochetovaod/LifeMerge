import 'package:flutter/material.dart';

import '../../domain/task.dart';

class TaskFormSheet extends StatefulWidget {
  const TaskFormSheet({
    super.key,
    this.initialTask,
    this.initialTitle,
    this.initialDescription,
    required this.onSubmit,
  });

  final Task? initialTask;
  final String? initialTitle;
  final String? initialDescription;
  final void Function(TaskDraft) onSubmit;

  @override
  State<TaskFormSheet> createState() => _TaskFormSheetState();
}

class _TaskFormSheetState extends State<TaskFormSheet> {
  final _formKey = GlobalKey<FormState>();
  late String _title;
  String? _description;
  DateTime? _dueAt;
  TaskPriority _priority = TaskPriority.medium;
  TaskStatus _status = TaskStatus.todo;
  int? _estimatedMinutes;

  @override
  void initState() {
    super.initState();
    final task = widget.initialTask;
    if (task != null) {
      _title = task.title;
      _description = task.description;
      _dueAt = task.dueAt;
      _priority = task.priority;
      _status = task.status;
      _estimatedMinutes = task.estimatedMinutes;
    } else {
      _title = widget.initialTitle ?? '';
      _description = widget.initialDescription;
    }
  }

  Future<void> _pickDueDate() async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: _dueAt ?? now,
      firstDate: now.subtract(const Duration(days: 365)),
      lastDate: now.add(const Duration(days: 365)),
    );
    if (picked != null) {
      setState(() {
        _dueAt = picked;
      });
    }
  }

  void _submit() {
    final isValid = _formKey.currentState?.validate() ?? false;
    if (!isValid) return;
    _formKey.currentState?.save();
    widget.onSubmit(
      TaskDraft(
        title: _title.trim(),
        description: _description?.trim(),
        dueAt: _dueAt,
        priority: _priority,
        status: _status,
        estimatedMinutes: _estimatedMinutes,
      ),
    );
    Navigator.of(context).pop();
  }

  @override
  Widget build(BuildContext context) {
    final isEditing = widget.initialTask != null;
    return Padding(
      padding: EdgeInsets.only(
        bottom: MediaQuery.of(context).viewInsets.bottom,
      ),
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: <Widget>[
              Container(
                width: 48,
                height: 4,
                margin: const EdgeInsets.only(bottom: 12),
                decoration: BoxDecoration(
                  color: Theme.of(context).colorScheme.outline,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              Text(
                isEditing ? 'Edit task' : 'New task',
                style: Theme.of(context).textTheme.titleLarge,
              ),
              const SizedBox(height: 12),
              TextFormField(
                initialValue: _title,
                decoration: const InputDecoration(labelText: 'Title'),
                onSaved: (value) => _title = value ?? '',
                validator: (value) {
                  if (value == null || value.trim().isEmpty) {
                    return 'Title is required';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 12),
              TextFormField(
                initialValue: _description,
                decoration: const InputDecoration(labelText: 'Description'),
                maxLines: 3,
                onSaved: (value) => _description = value,
              ),
              const SizedBox(height: 12),
              Row(
                children: <Widget>[
                  Expanded(
                    child: DropdownButtonFormField<TaskPriority>(
                      value: _priority,
                      decoration: const InputDecoration(labelText: 'Priority'),
                      items: TaskPriority.values
                          .map((priority) => DropdownMenuItem<TaskPriority>(
                                value: priority,
                                child: Text(priority.name.toUpperCase()),
                              ))
                          .toList(),
                      onChanged: (value) {
                        if (value != null) {
                          setState(() => _priority = value);
                        }
                      },
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: DropdownButtonFormField<TaskStatus>(
                      value: _status,
                      decoration: const InputDecoration(labelText: 'Status'),
                      items: TaskStatus.values
                          .map((status) => DropdownMenuItem<TaskStatus>(
                                value: status,
                                child: Text(status.name.toUpperCase()),
                              ))
                          .toList(),
                      onChanged: (value) {
                        if (value != null) {
                          setState(() => _status = value);
                        }
                      },
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Row(
                children: <Widget>[
                  Expanded(
                    child: TextFormField(
                      initialValue: _estimatedMinutes?.toString(),
                      decoration: const InputDecoration(labelText: 'Estimated minutes'),
                      keyboardType: TextInputType.number,
                      onSaved: (value) => _estimatedMinutes = int.tryParse(value ?? ''),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: _pickDueDate,
                      icon: const Icon(Icons.event),
                      label: Text(_dueAt != null
                          ? MaterialLocalizations.of(context).formatMediumDate(_dueAt!)
                          : 'Pick due date'),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _submit,
                  child: Text(isEditing ? 'Save changes' : 'Create task'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
