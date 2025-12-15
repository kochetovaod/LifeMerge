# Inbox API (v1)

## Общие правила
- Авторизация: `Authorization: Bearer <token>`, поддержка `Accept-Language` и `X-Timezone`.
- Все записи имеют `created_at`, `updated_at`, `deleted`; изменяющие операции требуют `request_id` или `X-Idempotency-Key`.
- Ответы и ошибки следуют формату `{error: {code, message, details?}}` и всегда возвращают `request_id` для трассировки.
- Пагинация cursor-based (`cursor`, `limit`) с `next_cursor` в ответе.

## GET /v1/inbox
- Query: `status?`, `cursor?`, `limit?`
- Возвращает список входящих элементов с метаданными источника (`source`, `payload_type`).

## POST /v1/inbox
- Body: `{source, payload, request_id}` — создание входящего элемента (из виджета/интеграции).
- Для ассистента допускается `context` (текст) для последующей конвертации AI.

## POST /v1/inbox/{id}/convert
- Body: `{type: task|event|note, mapped_fields, request_id}` — конвертация во внутренние сущности.
- В ответе возвращается созданная сущность и обновлённый статус inbox-элемента.

## PATCH /v1/inbox/{id}
- Body: `{status?, payload?, request_id}` (статусы: new, converted, archived).
- При конфликте по `updated_at` возвращается `409`.

## DELETE /v1/inbox/{id}
- Body: `{request_id}`

Ответы содержат `created_at` и `updated_at`, пригодны для офлайн-синхронизации.
