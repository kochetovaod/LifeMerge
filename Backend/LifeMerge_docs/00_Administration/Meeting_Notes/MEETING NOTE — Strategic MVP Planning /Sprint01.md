## Sprint 01 Backlog — LifeMerge

### 🔖 Эпики (M0–M7)

* **M0 – Skeleton & Infrastructure**
* **M1 – Auth & Onboarding**
* **M2 – Tasks MVP**
* **M3 – Calendar Day MVP**
* **M4 – Inbox MVP**
* **M5 – Notifications Infra**
* **M6 – Analytics Events (A1)**
* **M7 – AI Planner v1 (Stub & Contracts)**

---

### 🧩 Бэклог задач по эпикам

#### 🟦 M0 – Skeleton & Infrastructure

* **[P0] Init project architecture (Mobile skeleton)**
  Assignee: Даниил
  Desc: DI, router shell, layer separation, navigation container
  Status: In Progress
  DoR: структура слоёв согласована, shell-роутинг определён

* **[P0] Storage Layer + SecurePrefs abstraction**
  Assignee: Дмитрий
  Desc: key-value + encrypted storage, clear interfaces
  DoR: согласованы контракты offline-хранилища

* **[P1] AppTheme / Tokens integration**
  Assignee: Дмитрий
  Figma: [Ready for Dev → Theme tokens](https://www.figma.com/file/xyz/ready-for-dev?type=design&node-id=1001)
  Desc: типографика, цвета, spacing, радиусы — по токенам

* **[P1] Base UI Components (Buttons, TextFields, AppBars)**
  Assignee: Дмитрий
  Figma: [Ready for Dev → Components](https://www.figma.com/file/xyz/ready-for-dev?type=design&node-id=2002)
  Desc: Button, TextField, BottomNav, Sheet, Dialog — по токенам

---

#### 🟦 M1 – Auth & Onboarding

* **[P0] SignUp / SignIn / Forgot / Reset / Logout flows**
  Assignee: Дмитрий
  Figma: [Ready for Dev → Auth](https://www.figma.com/file/xyz/ready-for-dev?type=design&node-id=3010)
  Desc: форма, ошибки, интеграция с Auth API

* **[P0] RestoreSession & token refresh**
  Assignee: Даниил
  Desc: проверка токена, автоматическое восстановление

* **[P0] Onboarding flow + schedule setup**
  Assignee: Дмитрий
  Figma: [Ready for Dev → Onboarding](https://www.figma.com/file/xyz/ready-for-dev?type=design&node-id=3020)
  Desc: мастер из 3 экранов, график работы, завершение онбординга

---

#### 🟦 M2 – Tasks MVP

* **[P0] Task List UI + offline sync**
  Assignee: Дмитрий
  Figma: [Ready for Dev → Tasks List](https://www.figma.com/file/xyz/ready-for-dev?type=design&node-id=4001)
  Desc: список задач, offline состояние, pull-to-refresh

* **[P0] Create / Edit / Complete Task**
  Assignee: Даниил
  Figma: [Ready for Dev → Task Editor](https://www.figma.com/file/xyz/ready-for-dev?type=design&node-id=4002)
  Desc: поля: title, priority, due_at, estimated_min, goal_id (nullable)

* **[P1] Offline queue: Tasks CRUD**
  Assignee: Дмитрий
  Desc: очередь операций + conflict resolution по updated_at

---

#### 🟦 M3 – Calendar Day MVP

* **[P0] Calendar Day View: static timeline + event list**
  Assignee: Дмитрий
  Figma: [Ready for Dev → Calendar Day](https://www.figma.com/file/xyz/ready-for-dev?type=design&node-id=5001)
  Desc: отображение событий по времени, support offline read

* **[P0] Create Event: basic modal**
  Assignee: Даниил
  Figma: [Ready for Dev → Event Modal](https://www.figma.com/file/xyz/ready-for-dev?type=design&node-id=5002)
  Desc: без повторений, один слот, заглушка времени

---

#### 🟦 M4 – Inbox MVP

* **[P1] Inbox screen + record input**
  Assignee: Дмитрий
  Figma: [Ready for Dev → Inbox](https://www.figma.com/file/xyz/ready-for-dev?type=design&node-id=6001)
  Desc: запись текста, отображение списка

* **[P2] Convert Inbox Item → Task**
  Assignee: Даниил
  Desc: выбор действия при обработке inbox элемента

---

#### 🟦 M5 – Notifications Infra

* **[P1] Push infra + local permissions request**
  Assignee: Даниил
  Desc: подключение Firebase, регистрация токена, проверка разрешений

---

#### 🟦 M6 – Analytics Events (A1)

* **[P0] Send A1 events to debug: User_SignUp, Onboarding_Complete, Task_Created, Reached_Calendar**
  Assignee: Дмитрий
  Desc: логика вызова и параметров, интеграция в flow

---

#### 🟦 M7 – AI Planner v1 (Stub)

* **[P0] Validate Planner JSON schemas (tasks_min, calendar_min, preferences, goals_min)**
  Assignee: Игорь
  Desc: фиксация схем, валидация, sync с backend

* **[P1] /v1/ai/plan_week stub API**
  Assignee: Константин
  Desc: приём JSON, возвращение шаблонного плана, поля plan[], notes[], audit

* **[P1] Sample payloads: normal / overloaded / weekend-only**
  Assignee: Константин
  Desc: 3 заготовки, используемые для QA и Mobile интеграции
