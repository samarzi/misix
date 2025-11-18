# Implementation Plan

- [x] 1. Создать SQL миграцию для удаления email-аутентификации
  - Создать файл `backend/migrations/009_remove_email_auth.sql`
  - Добавить DROP COLUMN для email, password_hash, email_verified
  - Добавить ALTER COLUMN для telegram_id SET NOT NULL
  - Добавить DROP INDEX для idx_users_email
  - Сделать миграцию безопасной с проверками IF EXISTS
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 2. Создать Python скрипт для применения миграции
  - Создать файл `backend/apply_remove_email_migration.py`
  - Реализовать чтение и выполнение SQL миграции
  - Добавить проверку успешности применения
  - Добавить логирование результатов
  - _Requirements: 1.5_

- [ ] 3. Удалить/упростить backend auth компоненты
- [x] 3.1 Обновить auth router
  - Открыть `backend/app/api/routers/auth.py`
  - Удалить endpoints: /register, /login, /reset-password
  - Оставить только Telegram-related endpoints или удалить файл полностью
  - _Requirements: 2.1_

- [x] 3.2 Обновить auth service
  - Открыть `backend/app/services/auth_service.py`
  - Удалить методы email-аутентификации
  - Упростить до Telegram-only или удалить файл
  - _Requirements: 2.2_

- [x] 3.3 Обновить auth models
  - Открыть `backend/app/models/auth.py`
  - Удалить UserRegister, UserLogin, PasswordReset модели
  - Оставить только Telegram-related модели
  - _Requirements: 2.3_

- [x] 3.4 Упростить security module
  - Открыть `backend/app/core/security.py`
  - Удалить функции хеширования/верификации паролей
  - Оставить только JWT функции (если используются)
  - _Requirements: 2.4_

- [x] 3.5 Обновить API dependencies
  - Открыть `backend/app/api/deps.py`
  - Упростить get_current_user для Telegram-only
  - Удалить проверки email verification
  - _Requirements: 2.5_

- [ ] 4. Удалить frontend auth компоненты
- [x] 4.1 Обновить auth store
  - Открыть `frontend/src/stores/authStore.ts`
  - Удалить методы login, register, resetPassword
  - Упростить до Telegram-only
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 4.2 Обновить validation schemas
  - Открыть `frontend/src/lib/validation/schemas.ts`
  - Удалить email/password validation schemas
  - _Requirements: 3.5_

- [x] 4.3 Удалить auth UI компоненты
  - Найти и удалить компоненты форм входа/регистрации
  - Найти и удалить компоненты сброса пароля
  - Обновить роутинг если необходимо
  - _Requirements: 3.1, 3.2, 3.3_

- [ ] 5. Обновить документацию
- [x] 5.1 Обновить authentication docs
  - Открыть `backend/docs/AUTHENTICATION.md`
  - Переписать для описания только Telegram flow
  - Удалить все упоминания email/password
  - _Requirements: 4.1_

- [x] 5.2 Обновить environment examples
  - Открыть `backend/.env.example`
  - Удалить email-related переменные окружения
  - _Requirements: 4.3_

- [x] 5.3 Обновить README файлы
  - Обновить `README.md` в корне проекта
  - Обновить `backend/README.md`
  - Описать только Telegram-based setup
  - _Requirements: 4.1, 4.4_

- [x] 6. Исправить database validator
  - Открыть `backend/app/core/database.py`
  - Проверить метод test_write_operation()
  - Убедиться что не используются email поля
  - Убедиться что создается только telegram_id
  - _Requirements: 5.1, 5.2_

- [x] 7. Checkpoint - Применить миграцию и протестировать
  - Запустить скрипт применения миграции
  - Проверить схему БД (email колонки удалены, telegram_id NOT NULL)
  - Запустить database validator - должен пройти успешно
  - Перезапустить backend - должен стартовать без ошибок
  - Отправить сообщение боту - должен ответить и создать пользователя
  - Проверить frontend - нет форм email-аутентификации
  - _Requirements: 1.5, 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5, 5.1, 5.2, 5.3, 5.4_
