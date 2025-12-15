# Monitoring & Logging

## Метрики
- Backend: latency/таймауты по эндпоинтам, ошибки 4xx/5xx, очередь задач, использование БД (CPU, connections, slow queries).
- AI сервис: время ответа, количество токенов, процент fallbacks, очередь job'ов.
- Мобильный клиент: crash-free %, время запуска, FPS на ключевых экранах.

## Логирование
- Формат JSON, обязательные поля: `timestamp`, `level`, `service`, `request_id`, `user_id`, `path`, `latency_ms`.
- PII маскируем; отключаем body для финансовых операций.
- Корреляция через `request_id` между сервисами.

## Алёрты (пример)
- API error rate >5% за 5 минут.
- Latency p95 > 400 мс на `/tasks` или `/calendar`.
- Очередь фоновых задач > 1k сообщений 10 минут.
- Crash-free mobile < 98% за сутки.

## Дашборды
- Grafana/Datadog для сервисных метрик, Sentry для ошибок, Firebase Crashlytics для мобильных.
- Общий продуктовый дашборд: MAU, удержание D1/D7, активность по модулям (календарь, задачи, финансы).
