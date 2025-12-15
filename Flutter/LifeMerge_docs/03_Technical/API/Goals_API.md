# Goals API (v1)

## Общие правила
- Все запросы защищены Bearer JWT; заголовки `Accept-Language` и `X-Timezone` обязательны для корректного отображения сроков.
- Изменяющие операции требуют `request_id` или `X-Idempotency-Key` для идемпотентности (офлайн-режим, повторные отправки).
- Пагинация cursor-based: `cursor`, `limit`; ответы возвращают `next_cursor`.
- Ошибки оформляются как `{error: {code, message, details?}}`; при конфликте по `updated_at` возвращается `409`.

## GET /v1/goals
- Query: `status?`, `area?`, `cursor?`, `limit?`
- Ответ дополнительно отдаёт агрегаты по связанным задачам (`tasks_open`, `tasks_done`).

## POST /v1/goals
- Body: `{title, description?, area?, target_date?, request_id}`
- При создании можно передать стартовый `progress` и список связанных `task_ids`.

## PATCH /v1/goals/{id}
- Body: `{title?, description?, area?, target_date?, status?, progress?, request_id}`
- При смене статуса на `completed` фиксируется `completed_at`.

## DELETE /v1/goals/{id}
- Soft delete; body `{request_id}`.
- Удаление каскадно архивирует связанные задачи (статус deferred).

## Метрики и прогресс
- `GET /v1/goals/{id}/progress` — агрегированный прогресс по задачам.
- `POST /v1/goals/{id}/progress` — ручное обновление прогресса `{progress, note?, request_id}`.
- Ответ включает связанные активные задачи (до 5) для виджета «Фокус дня».
