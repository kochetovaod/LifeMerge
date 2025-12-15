# Mobile Architecture (Flutter)

## Слои
- **Presentation:** `views`, `widgets`, `state` (riverpod/provider), маршруты через `go_router`.
- **Domain:** use-cases (например, `planWeek`, `syncTasks`), модели без зависимостей на Flutter.
- **Data:** репозитории (API + локальное хранилище), мапперы DTO ↔ domain, кеширование.
- **Infrastructure:** HTTP клиент, secure storage, аналитика, пуши.

## Офлайн/онлайн
- Локальная БД `sqflite` содержит задачи, события, транзакции, цели, очереди операций.
- При отсутствии сети операции складываются в `pending_operations` с `request_id`; синк при восстановлении соединения.
- Конфликты: правило «сервер выигрывает», но UI показывает diff и позволяет принять локальную версию.

## Навигация и модули
- Отдельные модули: `auth`, `tasks`, `calendar`, `goals`, `finance`, `inbox`, `settings`.
- Common UI: `lifemerge_theme`, `AppScaffold`, `primary_button`, `sheet_header` из UI Kit.

## Тестирование
- Widget тесты для списков задач, календаря, финансовых графиков.
- Golden тесты для базовых компонентов UI Kit.
- Интеграционные тесты сценариев: онбординг, создание задачи, офлайн-режим.
