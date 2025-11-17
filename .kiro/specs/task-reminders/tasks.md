# Implementation Plan - Task Reminders

- [x] 1. Подготовить базу данных
  - Добавить поле last_reminder_sent_at в таблицу tasks
  - Создать таблицу user_settings для настроек напоминаний
  - Создать индекс на deadline для быстрого поиска
  - Создать миграцию 005_add_reminders.sql
  - _Requirements: 1.1, 3.5_

- [x] 2. Создать ReminderService
  - Создать backend/app/services/reminder_service.py
  - Реализовать метод check_reminders() для проверки задач
  - Реализовать метод send_daily_summary() для утренней сводки
  - Реализовать логику определения когда отправлять напоминание
  - Добавить обработку ошибок и retry логику
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4, 5.2, 5.3, 5.4_

- [x] 3. Создать TelegramNotifier
  - Создать backend/app/bot/notifier.py
  - Реализовать send_reminder() для отправки напоминаний
  - Реализовать send_summary() для отправки сводки
  - Реализовать форматирование сообщений с эмодзи
  - Добавить inline кнопки (Выполнено/Отложить)
  - Обработать ошибки отправки (user blocked bot)
  - _Requirements: 1.4, 2.1, 2.2, 2.3, 2.4, 4.1, 4.2, 4.3, 4.4, 4.5, 5.2_

- [x] 4. Настроить APScheduler
  - Создать backend/app/bot/scheduler.py
  - Настроить AsyncIOScheduler
  - Добавить job для check_reminders (каждые 5 минут)
  - Добавить job для daily_summary (9:00 утра)
  - Реализовать graceful shutdown
  - Добавить error handling и auto-restart
  - _Requirements: 1.1, 2.1, 5.1, 5.5_

- [x] 5. Интегрировать scheduler в бота
  - Обновить backend/app/bot/__init__.py
  - Запустить scheduler при старте бота
  - Остановить scheduler при shutdown
  - Передать bot instance в notifier
  - _Requirements: 1.1, 5.5_


- [x] 6. Добавить команду /reminders
  - Обновить backend/app/bot/handlers/command.py
  - Реализовать handle_reminders_command()
  - Показать текущие настройки пользователя
  - Добавить inline кнопки для изменения настроек
  - Реализовать callback handlers для кнопок
  - Сохранять изменения в user_settings
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 7. Расширить TaskRepository
  - Добавить метод get_tasks_needing_reminders()
  - Добавить метод update_last_reminder_sent()
  - Добавить метод get_user_tasks_for_today()
  - Добавить метод get_overdue_tasks()
  - Добавить метод get_completed_yesterday_count()
  - _Requirements: 1.1, 1.2, 1.3, 2.2, 2.3, 2.4_

- [x] 8. Создать UserSettingsRepository
  - Создать backend/app/repositories/user_settings.py
  - Реализовать get_settings() с дефолтными значениями
  - Реализовать update_settings()
  - Реализовать get_all_users_with_reminders_enabled()
  - _Requirements: 3.2, 3.3, 3.4, 3.5_

- [ ]* 9. Добавить мониторинг
  - Логировать количество отправленных напоминаний
  - Логировать ошибки отправки
  - Добавить метрики в health check
  - Отслеживать время выполнения jobs
  - _Requirements: 5.4_

- [ ]* 10. Написать тесты
  - Unit тесты для ReminderService
  - Unit тесты для форматирования сообщений
  - Integration тесты для scheduler
  - Mock тесты для Telegram API
  - _Requirements: 1.1, 2.1, 4.1, 5.1_
