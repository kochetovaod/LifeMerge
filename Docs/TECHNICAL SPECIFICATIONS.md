# 🧩 **TECHNICAL SPECIFICATIONS — LifeMerge**

---

# 1. Архитектура системы

## 1.1. Общая архитектура

LifeMerge — это **клиент-серверная** система:

* **Frontend:** Flutter-приложение (iOS + Android)
* **Backend API:** REST / JSON
* **AI-модуль:** отдельный сервис (может быть Python/Node), вызываемый через REST
* **База данных:** PostgreSQL
* **Сервис фоновых задач:** Celery / Sidekiq / BullMQ (зависит от backend stack)
* **Push-уведомления:** Firebase Cloud Messaging (Android), APNs (iOS)
* **Аналитика:** Mixpanel/Amplitude + серверные события

Архитектура уровня продукта:

```
┌───────────────────────────┐
│         Flutter App        │
│  (Presentation + Logic)    │
└──────────────┬────────────┘
               │ REST / WebSocket (later)
┌──────────────┴────────────┐
│         Backend API        │
│  Auth, Calendar, Tasks,    │
│  Finance, Goals, Billing   │
└──────────────┬────────────┘
               │
      ┌────────┴─────────┐
      │    AI Service     │
      │ (Planner, Insights)│
      └────────┬──────────┘
               │
      ┌────────┴──────────┐
      │   PostgreSQL DB    │
      └────────────────────┘
```

---

# 2. Архитектура Flutter-клиента

## 2.1. Структура приложения

Используем слоистую архитектуру:

### **1) Presentation Layer**

* UI (Flutter Widgets / Material 3 / Custom components)
* State management: **Riverpod** (Providers + Notifiers)

### **2) Domain Layer**

* Entities (Task, Goal, Event, FinanceRecord, UserSettings)
* UseCases (например: CreateTask, GenerateAIPlan)

### **3) Data Layer**

* Repositories (abstract → implement: remote + local)
* Data sources:

  * RemoteDataSource (Dio)
  * LocalDataSource (Hive/sqflite)
  * SyncQueue (offline)

### **4) Core**

* Exceptions
* Helpers
* Constants
* Logging
* Env variables

---

## 2.2. Папочная структура

```
lib/
  core/
    errors/
    utils/
    theme/
    localization/
  features/
    auth/
    calendar/
    tasks/
    goals/
    finance/
    inbox/
    ai_planner/
    settings/
  data/
    repositories/
    datasources/
    models/
  domain/
    entities/
    usecases/
  app.dart
  main.dart
```

---

# 3. Технологический стек

## Flutter (Frontend)

* **Language:** Dart 3.x
* **Framework:** Flutter 3.x
* **State:** Riverpod
* **Networking:** Dio
* **Local storage:** Hive или sqflite
* **Background tasks:** Workmanager (Android) + BGTasks (iOS) для синхронизации
* **Push:** Firebase Messaging
* **Crash reports:** Sentry или Firebase Crashlytics
* **Analytics:** Amplitude / Mixpanel

## Backend

* Language: **Node.js (NestJS)** или **Python (FastAPI)**
  (рекомендация — FastAPI для AI-интеграций или NestJS для структурности)
* Database: PostgreSQL
* ORM: Prisma / SQLAlchemy
* Queue: Redis + BullMQ / Celery
* AI service: Python (LangChain + OpenAI API / Local models)

---

# 4. Модель данных (DB Schema)

## 4.1. Таблица Users

| Поле          | Тип      | Описание       |
| ------------- | -------- | -------------- |
| id            | UUID     | PK             |
| email         | string   | уникальный     |
| password_hash | string   |                |
| timezone      | string   |                |
| currency      | string   |                |
| is_pro        | boolean  | подписка       |
| trial_end     | datetime | дата окончания |
| created_at    | datetime |                |
| updated_at    | datetime |                |

---

## 4.2. Goals (цели)

| Поле        | Тип       |
| ----------- | --------- |
| id          | UUID      |
| user_id     | FK        |
| title       | string    |
| description | text      |
| category    | string    |
| deadline    | datetime? |
| progress    | float     |
| created_at  | datetime  |

---

## 4.3. Tasks

| Поле               | Тип                        |
| ------------------ | -------------------------- |
| id                 | UUID                       |
| user_id            | FK                         |
| goal_id            | FK?                        |
| title              | string                     |
| description        | text?                      |
| priority           | enum(P0,P1,P2)             |
| context            | string                     |
| energy             | enum(light,medium,heavy)   |
| estimated_duration | int (min)                  |
| deadline           | datetime?                  |
| is_recurring       | boolean                    |
| recurrence_rule    | string (RRULE)             |
| status             | enum(open, done, canceled) |
| created_at         | datetime                   |

---

## 4.4. CalendarEvents

| Поле              | Тип                                    |
| ----------------- | -------------------------------------- |
| id                | UUID                                   |
| user_id           | FK                                     |
| type              | enum(event, task_block, finance_event) |
| title             | string                                 |
| start_time        | datetime                               |
| end_time          | datetime                               |
| linked_task_id    | FK?                                    |
| linked_finance_id | FK?                                    |
| category          | string                                 |
| created_at        | datetime                               |

---

## 4.5. FinanceRecords

| Поле            | Тип                   |
| --------------- | --------------------- |
| id              | UUID                  |
| user_id         | FK                    |
| type            | enum(income, expense) |
| category        | string                |
| amount          | decimal               |
| currency        | string                |
| linked_event_id | FK?                   |
| is_recurring    | boolean               |
| recurrence_rule | string                |
| date            | datetime              |
| created_at      | datetime              |

---

## 4.6. InboxItems

| Поле       | Тип                             |
| ---------- | ------------------------------- |
| id         | UUID                            |
| user_id    | FK                              |
| text       | string                          |
| type       | enum(idea, task, goal, finance) |
| status     | enum(active, processed)         |
| created_at | datetime                        |

---

# 5. API Specification (REST)

Ниже — укрупнённая спецификация.

---

## 5.1. Auth API

### POST `/auth/register`

### POST `/auth/login`

### POST `/auth/refresh`

### POST `/auth/reset-password-request`

### POST `/auth/reset-password-confirm`

---

## 5.2. Calendar API

### GET `/calendar?from=&to=`

Возвращает события периода.

### POST `/calendar/event`

Создать событие.

### PATCH `/calendar/event/{id}`

### DELETE `/calendar/event/{id}`

---

## 5.3. Tasks API

### GET `/tasks`

### POST `/tasks`

### PATCH `/tasks/{id}`

### DELETE `/tasks/{id}`

### POST `/tasks/{id}/schedule`

Привязывает задачу к календарю.

---

## 5.4. Goals API

### GET `/goals`

### POST `/goals`

### PATCH `/goals/{id}`

### DELETE `/goals/{id}`

---

## 5.5. Finance API

### GET `/finance?from=&to=`

### POST `/finance`

### PATCH `/finance/{id}`

### DELETE `/finance/{id}`

---

## 5.6. Inbox API

### GET `/inbox`

### POST `/inbox`

### POST `/inbox/{id}/convert-to-task`

### POST `/inbox/{id}/convert-to-goal`

### POST `/inbox/{id}/convert-to-finance`

---

## 5.7. AI Planner API

### POST `/ai/plan`

**Body:**

```
{
  "tasks": [...],
  "calendar": [...],
  "rules": {...},
  "period_start": "...",
  "period_end": "..."
}
```

**Response:**

```
{
  "suggestions": [
    {
      "task_id": "...",
      "action": "schedule" | "move" | "unscheduled",
      "start_time": "...",
      "end_time": "..."
    }
  ]
}
```

---

# 6. Offline & Sync Architecture

## 6.1. Local cache

* Хранит:

  * события,
  * задачи,
  * цели,
  * финансы,
  * inbox.

## 6.2. Sync Queue (очередь синхронизации)

Каждое offline-действие создаёт **SyncEntry**:

```
{
  id,
  endpoint,
  method,
  payload,
  timestamp,
  status: pending/sent
}
```

При восстановлении сети:

* очередь проходит по FIFO;
* в случае конфликта → стратегия MVP:
  **последний апдейт побеждает (Last Write Wins)**.

## 6.3. Фоновая синхронизация (сервер)

* **Очередь sync**: серверный воркер (Celery/Redis) подтверждает и фиксирует входящие пачки sync-операций, отправляет 409 при `updated_at` конфликте, пишет ошибку в лог.
* **Крон-задачи**:
  * каждые 5 минут — обработка зависших sync операций (статус pending>5 минут) с повторной отправкой webhooks/FCM ack;
  * 02:00 local — генерация и отправка дневных дайджестов;
  * Понедельник 08:00 local — недельные дайджесты;
  * очистка старыx sync-логов >30 дней.
* **Политика повторов**: экспоненциальный backoff до 5 попыток, DLQ для ручного анализа.

---

# 7. Push Notifications

## iOS

* APNs через Firebase Messaging
* background notification handler

## Android

* Firebase Messaging

Типы пушей:

1. Начало события
2. Дедлайны задач
3. Финансовые события

### Push-канал и дайджесты

* **FCM/APNs**: токены устройств хранятся вместе с user_id и платформой. Для iOS используется `apns-priority=10` на срочные уведомления (событие/дедлайн), `5` — для дайджестов/обновлений.
* **Топики/лейблы**: per-user topic `user-{id}` для таргетированной доставки и групповая метка `digests` для массовых дайджестов по расписанию.
* **Дайджесты**:
  * **Ежедневный**: агрегирует задачи/события на день, просроченные элементы и ближайшие финансы.
  * **Еженедельный**: сводка целей, прогресса задач, крупных финансовых движений и рекомендаций AI.
* **Параметры запроса к FCM**: `priority=high`, `content-available=1`, `mutable-content=1` для iOS, collapsible ключ `digest-{day|week}` для предотвращения спама.
* **Трассировка**: request_id прокидывается в заголовок FCM и в payload для последующей корреляции логов.

---

# 8. AI Module Architecture

AI сервис — отдельное приложение:

### Input:

* список задач,
* расписание,
* пользовательские правила,
* ограничения (контексты, energy),
* желаемый период.

### Output:

* предложения расписания

### Методы:

* LLM-assisted reasoning
* Hard constraints engine
* Soft scoring heuristics

### Контроль ошибок:

* если AI не смог спланировать → вернуть пустой список
* клиент покажет сообщение
* fallback: "Распределите задачи вручную"

---

# 9. Analytics Specification

### Все события отправляются:

* через Firebase → BigQuery
  или
* напрямую в Amplitude / Mixpanel

### События:

* `task_created`
* `task_completed`
* `goal_created`
* `finance_record_created`
* `ai_plan_requested`
* `ai_plan_accepted`
* `ai_plan_rejected`
* `subscription_trial_started`
* `subscription_upgraded`
* `retention_login`

### Параметры:

* user_id
* timestamp
* device
* platform
* type (для задач/финансов/целей)

---

# 10. Security Requirements

1. Все запросы — **HTTPS**
2. JWT access + refresh
3. Пароли — **bcrypt**
4. Защита от:

   * brute force,
   * replay attacks,
   * rate limiting API
5. Доступ к AI API — только через backend (приложение не получает ключ напрямую).

---

# 11. API Versioning

Версионирование всегда через URL:

```
/api/v1/tasks
/api/v1/calendar
/api/v1/ai/plan
```

v2 появится при изменении структур данных.

---

# 12. CI/CD

## Mobile

* Codemagic или GitHub Actions
* Сборки:

  * dev build,
  * staging build,
  * production build.

## Backend

* GitHub Actions
* Автотесты
* Deploy в Docker/Kubernetes
* Blue-Green / Rolling updates

---

# 13. Хранилище и версии схем

* **Миграции**: Alembic, обязательные pr-checks, миграции именуются по сущности/версии (`tasks_v2_add_priority`).
* **Сущности в зоне контроля**: задачи, цели, события, финансы, подписки, AI-планы.
* **Политика обновлений**:
  * prod миграции — только forward; downgrade допускается на стейджинге;
  * для долгих изменений — паттерн expand/contract (добавить столбец → backfill → переключить → удалить старый).
* **Конфликты `updated_at`**: optimistic locking, при несовпадении `updated_at` — 409 + возврат текущей версии записи.
* **Seed/fixtures**: минимальные данные (тестовые категории финансов, валюты) через `alembic upgrade head --tag seed`.

---

# 14. Observability

* **Логирование**:
  * AI-запросы: prompt hash, модель, latency, размер токенов, статус (success/timeout/error), request_id;
  * Ошибки синка: user_id, endpoint, payload hash, попытка, статус очереди;
  * Push отправка: ответ FCM/APNs, device_id, topic, collapse_key.
* **Метрики** (Prometheus):
  * `push_delivery_success_total`, `push_delivery_failure_total` с лейблами platform/type;
  * `sync_queue_depth`, `sync_retry_total`, `sync_dead_letter_total`;
  * `ai_request_latency_ms`, `ai_tokens_total`.
* **Алерты**: SLA пушей <95% за 15 минут, рост DLQ >100, рост AI error rate >5%.

---

# 15. Фичефлаги и лимиты Free

* **Лимиты** (конфигурация backend + дублирование в клиенте для UX):
  * цели ≤5,
  * задачи ≤100,
  * один финансовый счёт.
* **Доступ к AI/аналитике**:
  * флаг `ai_planner_enabled` (per-user, default=true для Pro/Trial, false для Free после исчерпания квоты), лимит запросов в сутки;
  * аналитика: события отправляются всем, но продвинутые отчёты/инсайты — только при `analytics_pro=true`.
* **Конфигурация**: feature-флаги в консуле/ENV, кэширование в Redis на 5 минут, логирование попаданий в лимиты (429 + код ошибки `limit_exceeded`).

