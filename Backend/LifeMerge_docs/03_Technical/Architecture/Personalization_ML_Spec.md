# ML Personalization Module — Input/Output Specification

## Назначение
Модуль персонализации отвечает за подготовку признаков и вызов ML/LLM-модели, которая адаптирует планирование, подсказки и приоритеты под конкретного пользователя. Спецификация фиксирует контракт входных данных и ожидаемых выходов, чтобы бэкенд и AI-сервис были согласованы.

## Общие правила
- Все идентификаторы пользователей и устройств передаются в захешированном виде (`sha256(user_id)`).
- Часовой пояс обязателен, время — в ISO 8601 с таймзоной.
- Денежные суммы указываются в базовой валюте профиля, строки валют — по ISO 4217.
- Пустые поля не отправляются; для необязательных массивов допускается `[]`.

## Входные данные (Input)
JSON-пакет `PersonalizationContext` передается из backend в ML-сервис:

```json
{
  "user_profile": {
    "user_hash": "string",
    "locale": "ru-RU",
    "timezone": "Europe/Moscow",
    "work_pattern": "5/2",
    "focus_hours": [{"start": "09:00", "end": "12:00"}],
    "no_go_periods": [{"weekday": "sun", "reason": "rest"}]
  },
  "behavior": {
    "tasks": [
      {
        "id_hash": "string",
        "title": "string",
        "priority": "P0|P1|P2",
        "context": "home|office|mobile|travel|custom",
        "energy": "light|medium|heavy",
        "estimated_minutes": 45,
        "deadline": "2024-11-20T18:00:00+03:00",
        "status": "open|done|canceled",
        "created_at": "2024-11-10T07:00:00+03:00",
        "completed_at": "2024-11-11T09:20:00+03:00"
      }
    ],
    "events": [
      {
        "id_hash": "string",
        "type": "event|task_block|finance_event",
        "starts_at": "2024-11-14T10:00:00+03:00",
        "ends_at": "2024-11-14T11:00:00+03:00",
        "title": "string",
        "linked_task_id_hash": "string|null"
      }
    ],
    "goals": [
      {
        "id_hash": "string",
        "title": "string",
        "category": "career|health|finance|family|learning|other",
        "deadline": "2025-03-01T00:00:00+03:00",
        "progress": 0.35
      }
    ],
    "finance": {
      "currency": "RUB",
      "regular_cashflow": [{"type": "income|expense", "amount": 75000, "interval": "monthly", "next_date": "2024-12-01"}],
      "last_transactions": [{"amount": -1200, "category": "food", "ts": "2024-11-12T13:00:00+03:00"}]
    },
    "engagement": {
      "session_count_7d": 9,
      "task_completion_rate_7d": 0.62,
      "ai_plan_accept_rate": 0.74,
      "feedback_events": [{"type": "like|dislike", "subject": "ai_plan", "ts": "2024-11-11T10:00:00+03:00"}]
    }
  },
  "constraints": {
    "hard_rules": ["no_heavy_after_20:00", "min_gap_15m"],
    "max_daily_work_minutes": 480
  },
  "request": {
    "request_id": "uuid",
    "model_version": "string",
    "prompt_version": "string",
    "target_horizon": "day|week"
  }
}
```

### Поля и валидация
- `user_profile.work_pattern`: одно из `5/2`, `2/2`, `3/3`, `custom`.
- `behavior.tasks[].priority`: `P0` обязательно имеет `deadline`; `estimated_minutes` > 0.
- `behavior.events[]`: `starts_at < ends_at`; если `type == task_block`, поле `linked_task_id_hash` обязательно.
- `behavior.finance.regular_cashflow[].interval`: `daily|weekly|monthly|yearly`.
- `constraints.hard_rules`: набор строковых токенов, согласованных между backend и AI-сервисом.

## Выходные данные (Output)
Ответ ML-сервиса `PersonalizationResult` возвращается в backend:

```json
{
  "request_id": "uuid",
  "generated_at": "2024-11-13T08:00:00Z",
  "model_version": "string",
  "prompt_version": "string",
  "personalization": {
    "ranked_tasks": [
      {"task_id_hash": "string", "score": 0.87, "reason": "high priority before deadline"}
    ],
    "suggested_slots": [
      {
        "task_id_hash": "string",
        "starts_at": "2024-11-14T09:30:00+03:00",
        "ends_at": "2024-11-14T10:15:00+03:00",
        "confidence": 0.81
      }
    ],
    "nudges": [
      {"type": "habit|focus|finance|energy", "message": "Сделай тяжёлую задачу до 11:00", "priority": "high|medium|low"}
    ],
    "ab_experiment": {"cohort": "B", "features": {"tone": "direct", "slot_length": 45}},
    "profile_updates": {
      "detected_focus_hours": [{"start": "08:30", "end": "11:30"}],
      "preferred_contexts": ["office", "mobile"],
      "anomalies": ["low_completion_3d"]
    }
  },
  "constraints_applied": ["no_heavy_after_20:00", "min_gap_15m"],
  "safety": {"redacted_fields": ["title"], "tokens": 3240}
}
```

### Интерпретация выходов
- `ranked_tasks`: отсортированный список для рекомендаций и авто-планирования; `score` в диапазоне `[0,1]`.
- `suggested_slots`: кандидаты для вставки в календарь; backend валидирует конфликты перед сохранением.
- `nudges`: микро-рекомендации для уведомлений/баннеров; `priority` задаёт канал доставки.
- `ab_experiment`: выбранные параметры для текущего пользователя, чтобы фиксировать в аналитике.
- `profile_updates`: сигналы, которые можно сохранить в `user_settings` после подтверждения бизнес-логикой.
- `constraints_applied`: набор правил, учтённых при генерации, для аудита и дебага.
- `safety`: метаданные о редактировании текста и токенизации.

## Контроль качества
- Обязательные проверки на стороне backend: соответствие `request_id`, допустимость таймслотов, ограничения по рабочему времени и валюте.
- Логирование: сохраняем `request_id`, `model_version`, `prompt_version`, `hashes` сущностей, но не сохраняем исходные тексты задач/заметок.
- Метрики: точность принятия слотов, % выполненных задач из рекомендованных, CTR по `nudges`, доля пользователей с обновлёнными `focus_hours` после 7 дней.
