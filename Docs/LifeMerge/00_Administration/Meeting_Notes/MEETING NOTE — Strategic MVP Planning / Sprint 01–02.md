**MEETING NOTE — Strategic MVP Planning / Sprint 01–02**

**Проект:** LifeMerge
**Дата:** 12.12.2025
**Тип встречи:** Стратегическое планирование MVP (CEO-level)
**Модератор:** Олег (CEO / Founder)

**Участники:**

* Олег — CEO / Founder
* Антон — Product Manager
* Виктор — Product Analyst
* Борис — Lead UI/UX Designer
* Григорий — Interaction Designer
* Даниил — Tech Lead Mobile (Flutter)
* Дмитрий — Mobile Developer
* Егор — Backend Lead
* Евгений — Backend Developer
* Игорь — AI Lead
* Константин — AI Engineer
* Леонид — QA Lead
* Марк — QA Engineer

---

### 1. Цель встречи

1. Зафиксировать P1-ядро MVP согласно Vision / Roadmap / Charter.
2. Уточнить разделение функционала по Sprint 01 и Sprint 02.
3. Определить технические ограничения и риск-области (TZ, offline, AI Planner).
4. Раздать конкретные Action Items командам с ответственными.

---

### 2. Краткий итог обсуждения

* Подтвержден P1-scope MVP: Auth/Onboarding, Calendar Core (Day), Tasks Core, Goals (базово), Inbox, AI Planner v1 (Pro-only), Notifications, Offline Sync, Core Architecture.
* Уточнено разделение спринтов:

  * Sprint 01 — фундамент + A1 (Auth/Onboarding, Tasks CRUD без целей, Calendar Day без drag&drop, Inbox MVP, Notifications infra, аналитика для A1).
  * Sprint 02 — A2 + связки + AI Planner v1 skeleton (Goals, Task→Calendar, Calendar drag&drop, AI Planner v1, Goal Progress, Calendar Conflicts basic, Digest push).
* Зафиксированы ограничения MVP: 1 задача = 1 слот в календаре; простой рабочий график; AI Planner v1 без продвинутой персонализации.
* Подтверждена готовность Design (UI Kit v1.0, P1 wireframes, страница Ready for Dev).
* Подтверждена готовность Mobile skeleton к старту фич (слои, DI, навигация shell, storage-контракты).
* Backend подтвердил стабильность Auth/Tasks/Calendar API и требует жёсткой дисциплины по TZ/updated_at/request_id.
* AI определил минимальный контракт Planner v1 (Tasks, Calendar, Preferences, Goals, Metadata).
* QA сформулировал требования к качеству базовых модулей и базовый набор smoke-тестов для Sprint 01.

---

## 3. Decisions (Решения)

| #   | Решение                                                                                                                                                       | Обоснование                                                                                                   | Owner внедрения                |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- | ------------------------------ |
| D1  | Утверждено P1-ядро MVP: Auth/Onboarding, Calendar Day, Tasks, Goals (базово), Inbox, AI Planner v1 (Pro-only), Notifications, Offline Sync, Core Architecture | Соответствие Product Vision, Roadmap и Metrics Plan; ядро, на котором строится A1/A2 и дальнейшая монетизация | Олег / Антон                   |
| D2  | Разделение спринтов: Sprint 01 = фундамент + A1, Sprint 02 = A2 + AI Planner skeleton                                                                         | Снижение риска расползания скопа, фокус на быстрой активации и устойчивом фундаменте                          | Олег / Антон                   |
| D3  | В Sprint 01 реализуем Calendar Day без drag&drop и сложных recurrence                                                                                         | Ускорение time-to-value, уменьшение технической сложности и рисков миграций на старте                         | Антон / Даниил / Егор          |
| D4  | Вводим MVP-ограничение: 1 задача = 1 слот в календаре (no many-to-many)                                                                                       | Снижение сложности Calendar/Tasks/AI, уменьшение риска сложных миграций по связям                             | Антон / Егор                   |
| D5  | Рабочие графики в MVP реализуются в простом формате (без сложных паттернов и истории смен)                                                                    | Избежать высокой сложности в Calendar и Data Model на MVP-этапе                                               | Антон / Егор                   |
| D6  | AI Planner v1 на MVP работает как rule-based+LLM skeleton с минимальным контрактом (Tasks, Calendar, Preferences, Goals)                                      | Быстрый запуск Pro-ценности, минимизация рисков ML и сложности персонализации на старте                       | Олег / Игорь                   |
| D7  | Все времена храним в UTC, клиент передает TZ в заголовке; единый middleware для idempotency/updated_at/request_id                                             | Устойчивость Offline Sync, консистентность данных, снижение риска критических багов в проде                   | Егор / Даниил                  |
| D8  | Crash-free цель для MVP: ≥99% (цель после стабилизации — 99.5%+)                                                                                              | Поддержка премиального позиционирования продукта и Pro-монетизации                                            | Олег / Леонид                  |
| D9  | Обязательная аналитика для событий A1/A2 с первого релиза (User_SignUp, Onboarding_Complete, Task_Created, Calendar_Connected и др.)                          | Необходимо для измерения активации, конверсии в Pro и продуктовых решений                                     | Антон / Виктор / Даниил / Егор |
| D10 | Design-файлы P1 (UI Kit v1.0, Ready for Dev) считаются единственным источником правды для визуала и взаимодействий                                            | Устранение разночтений, ускорение разработки и QA, снижение design-debt                                       | Борис                          |
| D11 | AI Planner API и JSON-схемы фиксируются как отдельный контракт, backend агрегирует данные, клиент передает только период и request_id                         | Разделение ответственности, упрощение клиента, соблюдение AI Architecture                                     | Игорь / Егор                   |
| D12 | QA Definition of Ready/Done становится обязательной для задач Sprint 01, влияющих на A1/A2                                                                    | Защита от недоделанных задач в критичных сценариях, контроль качества с первого инкремента                    | Леонид / Антон                 |

---

## 4. Action Items

### 4.1 Product

| #  | Action Item                                                                                                                                                                    | Owner          | Deadline (относительно встречи) | Статус |
| -- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------- | ------------------------------- | ------ |
| P1 | Зафиксировать Sprint 01 Scope в формате Sprint Plan (Auth/Onboarding, Tasks CRUD без целей, Calendar Day basic, Inbox MVP, Notifications infra, аналитика A1) и завести в Jira | Антон          | 3 рабочих дня                   | Open   |
| P2 | Подготовить сводную таблицу DoR/DoD по модулям Sprint 01 (Auth, Onboarding, Tasks, Calendar Day, Inbox, Notifications, Analytics)                                              | Антон          | 3 рабочих дня                   | Open   |
| P3 | Формально описать A1/A2 сценарии и добавить их в Metrics Plan                                                                                                                  | Антон / Виктор | 5 рабочих дней                  | Open   |
| P4 | Синхронизировать Event Spec c фактическим scope Sprint 01 (A1-события)                                                                                                         | Виктор         | 5 рабочих дней                  | Open   |

### 4.2 Design

| #    | Action Item                                                                                                                                    | Owner    | Deadline       | Статус |
| ---- | ---------------------------------------------------------------------------------------------------------------------------------------------- | -------- | -------------- | ------ |
| Dsg1 | Подтвердить и заморозить список P1-экранов для Sprint 01; убедиться, что все состояния (empty/error/loading/offline) находятся в Ready for Dev | Борис    | 3 рабочих дня  | Open   |
| Dsg2 | Обновить Interaction Guidelines для A1-flow и Calendar Day без drag&drop                                                                       | Григорий | 5 рабочих дней | Open   |
| Dsg3 | Зафиксировать дизайн-токены (цвета, типографика, spacing, corner radius, состояния) и согласовать naming c mobile-командой                     | Борис    | 3 рабочих дня  | Open   |

### 4.3 Mobile

| #  | Action Item                                                                                                                          | Owner                              | Deadline                           | Статус |
| -- | ------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------- | ---------------------------------- | ------ |
| M1 | Завершить и зафиксировать skeleton архитектуры (слои, DI, навигация shell, storage-контракты)                                        | Даниил                             | до конца 1-й недели Sprint 01      | Open   |
| M2 | Реализовать Theme / Design System (AppTheme, типографика, colors, базовые компоненты) согласно токенам Figma                         | Даниил / Дмитрий                   | до середины Sprint 01              | Open   |
| M3 | Реализовать Auth/Onboarding (домен, состояние экранов, навигация, валидация, обработка ошибок) с интеграцией с Auth API по контракту | Дмитрий (под руководством Даниила) | до конца Sprint 01                 | Open   |
| M4 | Реализовать базовый Tasks CRUD (список, создание, редактирование, завершение) без целей                                              | Дмитрий                            | до конца Sprint 01                 | Open   |
| M5 | Реализовать Calendar Day: отображение событий + создание простого события, без drag&drop и сложных recurrence                        | Дмитрий                            | конец Sprint 01 / начало Sprint 02 | Open   |
| M6 | Реализовать offline-queue v1 для задач и событий (updated_at + request_id)                                                           | Даниил                             | до конца Sprint 01                 | Open   |
| M7 | Интегрировать аналитические события A1 (User_SignUp, Onboarding_Complete, Task_Created, Reached_Calendar)                            | Даниил / Дмитрий                   | до конца Sprint 01                 | Open   |

### 4.4 Backend

| #  | Action Item                                                                                                                        | Owner          | Deadline                                 | Статус  |
| -- | ---------------------------------------------------------------------------------------------------------------------------------- | -------------- | ---------------------------------------- | ------- |
| B1 | Реализовать Auth API (/signup, /login, /refresh, /forgot, /reset, /logout) согласно спецификации                                   | Егор / Евгений | до середины Sprint 01                    | Open    |
| B2 | Реализовать Tasks API (CRUD без подзадач/recurrence на MVP-этапе) с полями priority, estimated_minutes, due_at, status, goal_id    | Егор / Евгений | до конца Sprint 01                       | Open    |
| B3 | Реализовать Calendar Events API для Day View (CRUD + базовая логика без сложных recurrence)                                        | Егор / Евгений | конец Sprint 01 / начало Sprint 02       | Open    |
| B4 | Реализовать единый middleware для TZ/idempotency (UTC storage, TZ header, updated_at, request_id) и прокинуть во все критичные API | Егор           | до конца Sprint 01                       | Open    |
| B5 | Реализовать backend-агрегацию данных для AI Planner (tasks_min, calendar_min, preferences, goals_min)                              | Егор / Евгений | Sprint 02 (подготовка в конце Sprint 01) | Planned |

### 4.5 AI

| #   | Action Item                                                                                                                          | Owner                               | Deadline                                 | Статус  |
| --- | ------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------- | ---------------------------------------- | ------- |
| AI1 | Зафиксировать JSON-схемы минимального контракта Planner v1 (tasks_min, calendar_min, preferences, goals_min) и согласовать с backend | Игорь                               | 3 рабочих дня                            | Open    |
| AI2 | Реализовать stub-реализацию /v1/ai/plan_week (детерминированный шаблонный план)                                                      | Константин (под руководством Игоря) | Sprint 02 (подготовка в конце Sprint 01) | Planned |
| AI3 | Добавить audit-поля (request_id, user_hash, model_version, prompt_version) в AI сервис                                               | Игорь / Константин                  | Sprint 02                                | Planned |
| AI4 | Подготовить sample payloads (простая неделя, перегруженная неделя, выходные) для мобайла и QA                                        | Константин                          | до начала Sprint 02                      | Planned |

### 4.6 QA

| #   | Action Item                                                                                                  | Owner         | Deadline              | Статус |
| --- | ------------------------------------------------------------------------------------------------------------ | ------------- | --------------------- | ------ |
| QA1 | Сформировать Smoke Test Checklist для Sprint 01 (Auth, Navigation, Calendar Day basic, Tasks, Offline-queue) | Леонид / Марк | 5 рабочих дней        | Open   |
| QA2 | Оформить QA Definition of Ready/Done для задач Sprint 01, влияющих на A1/A2                                  | Леонид        | 5 рабочих дней        | Open   |
| QA3 | Настроить QA-стенд и debug-режим аналитики (видимость ключевых событий A1/A2)                                | Марк          | до середины Sprint 01 | Open   |
| QA4 | Подготовить e2e-сценарии для проверки TZ и offline-синхронизации (Tasks + Calendar)                          | Леонид / Марк | до конца Sprint 01    | Open   |
