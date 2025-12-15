# Deployment Guide

## Подготовка
- Проверить миграции БД и обратную совместимость API.
- Убедиться, что `OpenAPI.yaml` обновлён и прошёл валидацию.
- Настроить переменные окружения (см. Environments.md), обновить secrets в Vault.

## Backend/AI
1. Собрать образы `backend:<tag>` и `ai-service:<tag>`.
2. Применить Helm-чарты: `helm upgrade --install lifemerge-backend charts/backend -f values/<env>.yaml`.
3. Выполнить миграции: `alembic upgrade head` или `prisma migrate deploy` (в зависимости от стека).
4. Проверить readiness/liveness, метрики, отсутствие 5xx в логах.

## Мобильные клиенты
- iOS: `flutter build ipa --flavor <env>`; загрузить в TestFlight/App Store Connect.
- Android: `flutter build appbundle --flavor <env>`; загрузить в Play Console/внешние сторы.
- Проверить совместимость с минимальной поддерживаемой версией, обновить changelog.

## Проверки после релиза
- Smoke-тест: логин, создание задачи/события, синхронизация офлайн → онлайн, операция с финансами.
- Проверить алёрты, дашборды и crash-free; вернуть rollout, если error rate > допустимого порога.
