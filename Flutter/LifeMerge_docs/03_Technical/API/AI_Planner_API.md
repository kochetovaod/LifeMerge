# AI Planner API (v1)

## Общие правила
- Требуется Bearer JWT + заголовки `Accept-Language`, `X-Timezone`; лимит 5 запросов/мин на пользователя.
- Используем `request_id` или `X-Idempotency-Key` для отслеживания повторов, все ответы содержат `model_version`.
- Формат ошибок: `{error: {code, message, details?}}`; при недоступности LLM возвращается `503 ai_unavailable`.
- Поля `user_id` не передаются в LLM; вместо них хэш. Все вызовы проходят через сервис аудита с логированием промптов/ответов (без чувствительных данных).

## POST /v1/ai/plan_week
- Body: `{goals[], tasks[], calendar[], preferences{focus_hours[], sleep, timezone}, request_id}`
- Response: `{plan: [ {day, slots:[{starts_at, ends_at, type(task|focus|rest), task_id?}]} ], notes, model_version}`
- В ответ добавляется `request_id` и `generated_at`; сохраняется в таблицу `ai_plans` вместе с `X-AI-Model` и `X-Prompt-Version`.

## POST /v1/ai/insights
- Body: `{period, metrics, request_id}`
- Response: текстовые выводы и списки рекомендаций.
- Поддерживает параметр `tone` (friendly|neutral|direct) для адаптации копирайта.

## POST /v1/ai/rephrase
- Body: `{text, tone (friendly|formal), request_id}`
- Ответ содержит `variants[]` и оценку токсичности входного текста.

## Безопасность
- Требуется Bearer токен; лимит 5 запросов/мин на пользователя.
- Поля `user_id` не передаются в LLM; вместо них хэш.

## Версионирование
- Заголовок `X-AI-Model` и `X-Prompt-Version` для отслеживания качества; сохраняем в `ai_plans`.
