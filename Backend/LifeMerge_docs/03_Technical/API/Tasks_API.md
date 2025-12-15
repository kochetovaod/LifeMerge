# Tasks API (v1)

## Общие правила
- Требуется `Authorization: Bearer <token>`, `Accept-Language` и `X-Timezone` для корректных дат дедлайнов.
- Для всех изменяющих операций передаётся `request_id` или `X-Idempotency-Key` (гарантия идемпотентности при офлайн-синхронизации).
- Пагинация cursor-based: параметры `cursor`, `limit`; ответы возвращают `next_cursor`.
- Ошибки: `{error: {code, message, details?}}`, например `validation_error`, `not_found`, `conflict` (при обновлении устаревшей версии `updated_at`).

## GET /v1/tasks
- Query: `status?`, `goal_id?`, `due_from?`, `due_to?`, `cursor?`, `limit?`
- Response: список задач + `next_cursor`.
- У каждой записи есть `created_at`, `updated_at`, `deleted` для офлайн-режима.

## POST /v1/tasks
- Body: `{title, description?, goal_id?, due_at?, priority?, estimated_minutes?, energy_level?, request_id}`
- Response: созданная задача.
- При создании можно передать `reminder_at[]` для мгновенной подписки на напоминания.

## PATCH /v1/tasks/{id}
- Body: любые изменяемые поля + `request_id`.
- Конфликты по `updated_at` возвращают `409` с актуальной задачей в `details.current`.

## DELETE /v1/tasks/{id}
- Soft delete. Body: `{request_id}`.
- Удалённые задачи помечаются `deleted=true` и остаются доступными в истории синка.

## Подзадачи
- `POST /v1/tasks/{id}/subtasks` → `{title, request_id}`
- `PATCH /v1/subtasks/{subtask_id}` → `{title?, done?, request_id}`
- Подзадачи наследуют `updated_at` для разрешения конфликтов.

## Напоминания/статусы
- `POST /v1/tasks/{id}/status` → `{status, request_id}` (todo/in_progress/done/deferred)
- `POST /v1/tasks/{id}/reminders` → `{remind_at}`
- Ответы содержат `updated_at` для разрешения конфликтов офлайн-синхронизации.
