# Deployment Plan — Draft Environment CI/CD

## Цель
Описать, как черновой стенд (Draft) автоматически собирается и разворачивается из CI/CD, чтобы разработчики получали изолированные сборки для раннего тестирования без влияния на Dev/Stage/Prod.

## Триггеры и ветки
- **feature/** и **bugfix/**: авто-сборка и деплой чернового стенда по каждому push в MR/PR.
- **manual re-run**: ручной перезапуск job для восстановления стенда или проверки фиксов.
- **auto-cleanup**: тайм-аут жизни стенда 48 часов; после merge/close MR стенд уничтожается.

## Пайплайн
1. **Lint/Static Analysis**: `flutter analyze`, `dart test --coverage` для клиента; `pytest -q` и `ruff`/`eslint` для backend/AI.
2. **Сборка контейнеров**: BuildKit, теги `draft-<branch>-<sha>` публикуются в приватный registry.
3. **Деплой**: Helm-чарт в namespace `draft-<branch>` с `values/draft.yaml`; включаем mock-провайдеры внешних интеграций.
4. **Миграции**: `alembic upgrade head` / `prisma migrate deploy` против отдельной Draft-БД; обратная совместимость обязательна.
5. **Smoke-тест**: `scripts/smoke_draft.sh` — логин, создание задачи, синхронизация офлайн → онлайн.
6. **Отчёт**: URL стенда и артефакты сборки публикуются в MR/PR комментарии.

## Роллбек и очистка
- Helm rollback на предыдущий релиз (`helm rollback <release> 1`) по детекту 5xx/ошибок readiness.
- После merge/закрытия MR job `cleanup_draft` удаляет namespace, секреты и storage claims.

## Требования к секретам
- Secrets и токены берутся из Vault/KMS по пути `draft/<team>/<service>`; доступ ограничен service account CI.
- В пайплайне используются временные credentials (TTL ≤ 1 час), чтобы уборка не блокировалась утечками ключей.

## Логи и наблюдаемость
- Включен stdout/stackdriver/ELK сбор логов для всех pod в namespace `draft-*`.
- Метрики и алёрты общие с Dev, но с отдельными неймспейс-фильтрами; частота проверок раз в 5 минут.

## Передача в Dev/Stage
- Merge в `develop` переключает пайплайн на Dev по существующим правилам (см. CI_CD_Pipeline.md).
- Принятые фичи получают тег `draft-tested` в release notes, если smoke прошёл на черновом стенде.
