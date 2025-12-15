# Technical Specification (кратко)

- **Платформы:** Flutter iOS/Android, backend REST на FastAPI/Express, AI-сервис отдельный.
- **БД:** PostgreSQL, Redis для кеша и сессий.
- **Фичи MVP:** auth, задачи, календарь, цели, финансы, inbox, AI-планирование недели.
- **Интеграции:** Google/Apple Calendar, FCM/APNs, внешняя LLM API.
- **Офлайн:** локальная БД + очередь операций, конфликты по `updated_at`.
- **Обновления:** OpenAPI.yaml генерируется автоматически, мобильные клиенты через App Store/Play с feature flags.
