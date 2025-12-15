# Требования к API

- REST/JSON, префикс `/v1`, консистентные коды ошибок и тело `{error:{code,message,details}}`.
- Авторизация через Bearer JWT, поддержка refresh; все запросы по HTTPS.
- Пагинация cursor-based (`cursor`, `limit`), ответы с `next_cursor`.
- Идемпотентность: `X-Idempotency-Key` или `request_id` для изменяющих операций.
- Все ресурсы содержат `updated_at`, `created_at`, `deleted` (soft delete) для офлайн-синхронизации.
- Локализация через `Accept-Language`, часовой пояс через `X-Timezone`.
- Rate limit по IP и пользователю; отдельные квоты для AI-вызовов.
