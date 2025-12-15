# Auth API (v1)

## Общие правила
- Все ответы используют структуру ошибок `{error: {code, message, details?}}`; успешные ответы содержат `request_id` для трассировки.
- Авторизация по Bearer JWT в `Authorization`, кроме `/signup`, `/login`, `/refresh`, `/forgot`, `/reset`.
- Локализация через `Accept-Language`; часовой пояс клиента передаётся в `X-Timezone` и фиксируется в сессии.
- Для защищённых операций поддерживаются `X-Idempotency-Key` и `request_id` (обязательно для серверного аудита и офлайн-синхронизации).
- Все токены выдаются только по HTTPS; refresh токены привязаны к `device_id` и могут быть отозваны для конкретного устройства или всех устройств.

## POST /v1/auth/signup
- body: `{email, password, full_name?, timezone}`
- result: `{user, access_token, refresh_token}`
- Ограничение по частоте: rate limit на пользователя/IP для предотвращения брутфорса.

## POST /v1/auth/login
- body: `{email, password, device_id}`
- result: `{user, access_token, refresh_token}`
- Ответ включает `created_at`, `updated_at`, `deleted` флаг пользователя для корректного состояния клиента.

## POST /v1/auth/refresh
- body: `{refresh_token, device_id}`
- result: `{access_token}`
- При несовпадении `device_id` возвращаем `401` с кодом `refresh_invalid_device`.

## POST /v1/auth/logout
- headers: `Authorization`
- body: `{all_devices?: boolean}`
- result: `{success: true}`

## POST /v1/auth/forgot
- body: `{email}` → письмо с кодом/ссылкой
- Ответ содержит TTL кода и маскированный email назначения.

## POST /v1/auth/reset
- body: `{email, code, new_password}`
- После успешного сброса старые refresh токены инвалидируются.

Общие правила: rate limit для `/signup` и `/forgot`, ответы содержат `request_id`.
