# 📱 Mobile — Sprint 01 (Foundation + A1)

## EPIC M0 — Core App Skeleton & Infrastructure

### M0.1 Finalize App Skeleton

**Type:** Story
**Priority:** P0

**Scope:**

* Зафиксировать структуру слоёв: `presentation / application / domain / data / core`.
* Финализировать DI-контейнер (scope per feature).
* App bootstrap (env, flavors, error handling root).
* AppRouter + Shell (Auth / Calendar / Tasks / Inbox / Settings / Pro).

**DoD:**

* Проект собирается.
* Можно подключать фичи без правок core.
* Нет feature-to-feature зависимостей.

---

### M0.2 Core Storage (Secure + KV)

**Type:** Story
**Priority:** P0

**Scope:**

* `SecureStorage` (tokens, sensitive data).
* `KeyValueStorage` (flags, onboarding state, prefs).
* Чистые интерфейсы + реализации.

**Tech notes:**

* Без прямых зависимостей в features.
* Async-safe, ready для offline-first.

**DoD:**

* Используется в Auth и Onboarding.
* Покрыт базовыми unit-тестами.

---

## EPIC M1 — Theme & Design System

### M1.1 AppTheme & Tokens

**Type:** Story
**Priority:** P0

**Scope:**

* Light/Dark theme.
* Color tokens (semantic).
* Typography (H1–Caption).
* Spacing, radii.

**Tech notes:**

* Naming = UI Kit v1.0.
* Ни одного “raw color” в UI.

**DoD:**

* Theme используется по всему приложению.
* Токены — единственный источник правды.

---

### M1.2 Base UI Components

**Type:** Story
**Priority:** P0

**Scope:**

* Button (Primary / Secondary / Tertiary + loading/disabled).
* TextField (all states).
* AppBar.
* BottomNavigation.
* ModalSheet / Dialog.
* Loader / Skeleton.

**DoD:**

* Компоненты используются в Auth/Tasks/Calendar.
* Нет дублирующихся UI-реализаций.

---

## EPIC M2 — Navigation

### M2.1 App Navigation Shell

**Type:** Story
**Priority:** P0

**Scope:**

* Auth flow routes.
* Main shell (tabs).
* Guarded routes по AuthState.
* Placeholder routes для Sprint 02.

**DoD:**

* Навигация соответствует wireframes.
* После онбординга → Calendar Day.

---

## EPIC M3 — Auth & Onboarding (A1 critical)

### M3.1 Auth Domain

**Type:** Story
**Priority:** P0

**Scope:**

* Entities: User, AuthState.
* UseCases: signIn, signUp, refresh, logout, restoreSession.
* Repository interfaces.

**DoD:**

* Domain не зависит от Flutter/UI.
* Готово к mock/real data source.

---

### M3.2 Auth UI & State

**Type:** Story
**Priority:** P0

**Scope:**

* Login / Register / Recovery.
* Form validation.
* Error states.
* Loading states.

**Tech notes:**

* Riverpod.
* Single source of truth для AuthState.

**DoD:**

* Happy path A1 проходит ≤5 минут.
* Ошибки API корректно отображаются.

---

### M3.3 Onboarding Flow

**Type:** Story
**Priority:** P0

**Scope:**

* Onboarding screens.
* Persist onboarding completion.
* Transition → Main Shell.

**Analytics:**

* `Onboarding_Complete`.

**DoD:**

* Логируется один раз.
* Повторный запуск → onboarding не показывается.

---

## EPIC M4 — Tasks Core (CRUD)

### M4.1 Tasks Domain

**Type:** Story
**Priority:** P0

**Scope:**

* Task entity.
* Status lifecycle.
* CRUD use-cases.

**Constraints:**

* Без goals.
* Без recurrence.

---

### M4.2 Tasks UI

**Type:** Story
**Priority:** P0

**Scope:**

* Task List.
* Task Create/Edit.
* Complete task.

**Analytics:**

* `Task_Created`
* `Task_Completed`.

**DoD:**

* Работает offline (через queue).
* UI соответствует design states.

---

## EPIC M5 — Calendar Day (Basic)

### M5.1 Calendar Day View

**Type:** Story
**Priority:** P0

**Scope:**

* Day timeline.
* Event list.
* Empty/loading/offline states.

**Constraints:**

* No drag&drop.
* No recurrence.

---

### M5.2 Event Create (Basic)

**Type:** Story
**Priority:** P0

**Scope:**

* Create event.
* Simple start/end.
* Save to backend / queue.

**Analytics:**

* `Reached_Calendar`.

---

## EPIC M6 — Offline Queue v1

### M6.1 Offline Operations Queue

**Type:** Story
**Priority:** P0

**Scope:**

* Queue for Tasks + Events.
* request_id + updated_at.
* Retry & conflict-safe.

**Tech notes:**

* Единая реализация.
* Прозрачна для features.

**DoD:**

* Можно создавать задачи/ивенты offline.
* Синк без дублей.

---

## EPIC M7 — Analytics (A1)

### M7.1 Analytics Infrastructure

**Type:** Story
**Priority:** P0

**Scope:**

* AnalyticsService abstraction.
* Firebase + Amplitude.
* Debug logging.

---

### M7.2 A1 Events

**Type:** Story
**Priority:** P0

**Events:**

* User_SignUp
* Onboarding_Complete
* Task_Created
* Reached_Calendar

**DoD:**

* События не дублируются.
* Проверены на QA-стенде.

---

# ⏱️ Ownership

* **Даниил:** архитектура, M0, M1, M6, аналитика, ревью.
* **Дмитрий:** реализация M2–M5 под контролем.
