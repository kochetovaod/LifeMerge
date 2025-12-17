# Deploy (Stage/Prod)

## Preconditions
- PostgreSQL доступен
- ENV=stage или ENV=prod
- DATABASE_URL задан

## Migrations (required)
Перед запуском приложения обязательно применить миграции:

```bash
alembic upgrade head
```

## Start

Запуск приложения (пример):

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Notes

* В stage/prod приложение не стартует, если миграции не применены или версия схемы БД не совпадает с Alembic head.

````