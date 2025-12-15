# CI/CD Pipeline

## CI (pull request)
1. Lint/format: `dart format --set-exit-if-changed`, `flutter analyze`, `ruff`/`eslint` для бекенда/AI.
2. Unit/widget tests: `dart test`, `pytest`, `npm test` (если фронт веб).
3. Сборка мобильного клиента в `--debug` для smoke, выгрузка артефактов в CI.
4. Генерация OpenAPI и проверка `scripts/validate_openapi.sh`.

## CD
- **Develop → Dev**: авто-деплой backend/AI через Docker + Helm, прогон миграций, загрузка демоданных.
- **Release candidate → Stage**: ручной триггер, подпись мобильных билдов (internal test), прогон регресса.
- **Prod**: мажорные релизы через change approval, канареечный rollout 10% → 50% → 100% за 24 часа.

## Артефакты
- Контейнеры собираются через BuildKit, публикуются в приватный registry.
- Мобильные `.ipa/.aab` хранятся в артефакт-репозитории с метаданными версии, commit SHA, окружения.

## Качество
- Codecov/coveralls с порогом >70% для ключевых модулей (tasks, calendar, finance).
- SAST/Dependency scan (Trivy/Snyk) обязательны перед stage/prod.
