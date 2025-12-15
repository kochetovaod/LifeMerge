# Calendar API (v1)

## Общие правила
- Требуется `Authorization: Bearer <token>`, заголовки `Accept-Language` и `X-Timezone` для корректного расчёта повторений и длительности.
- Идемпотентность через `request_id` или `X-Idempotency-Key` для всех операций создания/изменения/удаления.
- Ошибки в формате `{error: {code, message, details?}}`; при конфликте `updated_at` возвращается `409` с актуальным событием.
- Ответы включают `created_at`, `updated_at`, `deleted`, `source` (lifemerge/google/apple) для офлайн-синхронизации и разрешения конфликтов.

## GET /v1/calendar/events
- Query: `from`, `to`, `cursor?`, `limit?`, `sources?` (lifemerge/google/apple)
- Пагинация cursor-based; ответ содержит `next_cursor`.

## POST /v1/calendar/events
- Body: `{title, starts_at, ends_at, location?, recurrence_rule?, task_id?, source?, request_id}`
- При `task_id` создаётся привязка задачи к слоту.
- Принимаются временные зоны в ISO-8601; сервер нормализует к TZ пользователя.

## PATCH /v1/calendar/events/{id}
- Body: `{title?, starts_at?, ends_at?, location?, recurrence_rule?, request_id}`
- Для правок серии допускается `apply_to` (this|future|all) в `details`.

## DELETE /v1/calendar/events/{id}
- Soft delete; body `{request_id}`
- Для повторяющихся событий поддерживается `scope` (this|future|all).

## Синхронизация
- `POST /v1/calendar/import` — подключение внешнего календаря (OAuth token в защищённом хранилище).
- `POST /v1/calendar/webhook/google` — точка для уведомлений; подписки на 60 дней вперёд.
- Все события содержат `updated_at` и `source` для разрешения конфликтов.
