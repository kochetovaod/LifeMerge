## Metrics Plan — A1 / A2 / Core Metrics (Обновлён)

### A1 Activation (Sprint 01)

| Event               | Trigger                                           | Notes                             |
| ------------------- | ------------------------------------------------- | --------------------------------- |
| User_SignUp         | Завершена регистрация                             | email + метод                     |
| Onboarding_Complete | Пройден мастер онбординга                         | выбран график, дошёл до календаря |
| Task_Created        | Создана первая задача                             | через Task Editor                 |
| Reached_Calendar    | Пользователь открыл Calendar Day после онбординга | первый вход в планировщик         |

### A2 Activation (Sprint 02)

| Event                     | Trigger                                         | Notes                   |
| ------------------------- | ----------------------------------------------- | ----------------------- |
| Goal_Created              | Создана новая цель                              | через Goal Editor       |
| Task_Linked_To_Goal       | Привязана задача к цели                         | через goal_id           |
| Task_Attached_To_Calendar | Задача получила слот в календаре                | manual или drag         |
| AI_Planner_Used           | Пользователь нажал кнопку «Спланировать неделю» | даже если план заглушка |

### AI Metrics

| Event             | Trigger                                | Notes                 |
| ----------------- | -------------------------------------- | --------------------- |
| AI_Plan_Received  | Planner вернул plan[]                  | успешно, без ошибок   |
| AI_Plan_Confirmed | Пользователь применил план             | через UI принятия     |
| AI_Plan_Rejected  | Пользователь отменил предложенный план | измеряет недоверие/UX |

### Retention / WPAR Contribution

* WPAR = Weekly Planning Attachment Rate: есть ли цель → задачи → слот?
* Повторное использование Planner = proxy на perceived value
* Повторное создание целей = прокси на долгосрочную вовлечённость
