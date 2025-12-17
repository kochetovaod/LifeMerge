# MVP Scope v1 — LifeMerge (обновлено)

## Таблицы Alembic, входящие в MVP

| Таблица          | Входит в v1 | Обязательные поля                        | Best Effort поля               | Комментарий                  |
| ---------------- | ----------- | ---------------------------------------- | ------------------------------ | ---------------------------- |
| goals            | ✅           | id, user_id, title, progress, created_at | description, deadline          | goal_id используется в tasks |
| calendar_events  | ✅           | id, user_id, title, start_at, end_at     | location, recurrence           | без сложных recurrence       |
| finance_records  | ✅           | id, user_id, amount, type, category_id   | notes, recurrence              | базовые категории            |
| inbox_items      | ✅           | id, user_id, text, created_at            | type, processed_at             | конвертация в задачи/события |
| planner_requests | ✅           | id, user_id, plan[], notes[], metadata   | rejected_items, schedule_score | только stub + audit          |
| notifications    | ✅           | id, user_id, type, payload, send_at      | channel, is_muted              | базовые напоминания          |
| subscriptions    | ✅           | id, user_id, type, start_at, expires_at  | source, payment_method         | Trial/Pro логика             |

## Offline Sync (v1)

* Очередь операций через `sync_operations` (тип, объект, payload, updated_at, request_id)
* Объединение и передача пачкой через `/api/v1/batch-sync` (JSON array, header: timezone, request_id, client)
* Конфликты: стратегия LWW (last-write-wins) на backend, UI показывает дифф
* Поддерживаются: calendar_events, tasks, inbox, goals, finance_records
* Инфраструктура: sync queue, local cache (sqflite), auto-sync on reconnect, manual pull

## AI Planner v1 — бизнес-правила (MVP)

* Цель: расписать задачи на неделю с учётом слотов и user prefs
* Входные данные:

  * `tasks_min`: title, estimated_min, priority, due_at, goal_id
  * `calendar_min`: start_at, end_at, is_blocked
  * `preferences`: рабочие часы, forbidden windows, выходные
  * `goals_min`: goal_id, target_date, importance
  * `metadata`: request_id, user_hash, tz
* Результат:

  * plan[]: task_id, slot_start, slot_end
  * notes[]: типы предупреждений (buffer, conflict, weekend)
* Бизнес-правила:

  * Конфликт = ≥15 мин пересечения
  * Warning = слот < 10 мин буфера или вне рабочего окна
  * AI не перезаписывает календарь без запроса пользователя
  * Audit: model_version, prompt_version, request_id, debug_mode

## Feature Gating: Free / Trial / Pro

| Возможность                  | Free    | Trial | Pro |
| ---------------------------- | ------- | ----- | --- |
| AI Planner                   | ❌       | ✅     | ✅   |
| Кол-во целей                 | до 5    | ∞     | ∞   |
| Кол-во задач                 | до 100  | ∞     | ∞   |
| Финансовые категории         | базовые | все   | все |
| Уведомления                  | базовые | все   | все |
| Подробные объяснения Planner | ❌       | ✅     | ✅   |
| Отчёты по продуктивности     | ❌       | ✅     | ✅   |
| Custom правила AI (prefs)    | ❌       | ✅     | ✅   |

## Подтверждённые API-контракты (MVP)

* `/api/v1/tasks` — GET, POST, PATCH, DELETE; поддерживает `goal_id`, `estimated_min`, `is_synced`
* `/api/v1/batch-sync` — POST array объектов + headers (request_id, timezone)
* `/api/v1/planner/plan_week` — POST: tasks_min[], calendar_min[], prefs → возвращает plan[], notes[], audit
* `/api/v1/productivity/summary` — GET метрик: task-to-calendar rate, goal progress, WPAR

Все контракты валидированы backend и покрыты тестами QA (см. Decisions_Log.md).
