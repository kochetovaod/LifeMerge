# Finance API (v1)

## Общие правила
- Все запросы требуют Bearer JWT, а также заголовки `Accept-Language` и `X-Timezone` для нормализации дат и валютных обозначений.
- Для операций записи используем `request_id` или `X-Idempotency-Key`; ответы содержат `created_at`, `updated_at`, `deleted`.
- Пагинация cursor-based (`cursor`, `limit`); формат ошибок `{error: {code, message, details?}}`.
- Все суммы передаются в минорных единицах (integer) или decimal строго с указанием `currency`.

## Категории
- `GET /v1/finance/categories` — список (с `next_cursor` при пагинации).
- `POST /v1/finance/categories` — `{name, type: income|expense, color?, request_id}`
- `PATCH /v1/finance/categories/{id}` — обновление.

## Транзакции
- `GET /v1/finance/transactions` — фильтры: `from`, `to`, `category_id`, `cursor`, `limit`.
- `POST /v1/finance/transactions` — `{amount, currency, category_id?, happened_at, note?, request_id}`
- `PATCH /v1/finance/transactions/{id}` — любые поля + `request_id`.
- `DELETE /v1/finance/transactions/{id}` — soft delete.

## Бюджеты и отчёты
- `POST /v1/finance/budgets` — `{category_id?, period_start, period_end, limit_amount, currency, request_id}`
- `GET /v1/finance/summary` — агрегаты по периодам, прогноз до конца месяца, перерасход.
- Все отчёты содержат поле `currency` и временные интервалы, нормализованные к TZ пользователя.

Все суммы в API передаются в копейках/центах (integer) либо decimal, согласовано по `currency`.
