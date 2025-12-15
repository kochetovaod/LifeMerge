# CI Test Config

- Запуск `dart test` и `flutter test --tags=smoke` на каждом PR.
- Backend/AI: `pytest -q`, `npm test` (если Node), покрытие >70% для ядра.
- Lint: `dart format --set-exit-if-changed`, `flutter analyze`, `ruff`, `eslint`.
- Интеграционные тесты (эмуляторы) ночью по расписанию: онбординг, создание задачи, синк офлайн → онлайн.
- Отчёты в CI: JUnit + coverage, отправка в Codecov; уведомления в Slack/Telegram при падениях.
