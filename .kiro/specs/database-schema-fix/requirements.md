# Requirements Document

## Introduction

Приложение MISIX имеет критическую проблему схемы базы данных, которая не позволяет боту корректно работать. Таблица `users` имеет ограничения NOT NULL на колонках `email` и `password_hash`, но приложение использует только Telegram-аутентификацию и не использует email вообще. Тест валидации базы данных падает, потому что пытается создать Telegram-пользователя без email credentials.

## Glossary

- **System**: Backend приложения MISIX
- **Users Table**: PostgreSQL таблица для хранения информации о пользователях
- **Telegram User**: Пользователь, который аутентифицируется через Telegram bot используя telegram_id
- **Database Validator**: Компонент, который тестирует подключение к базе данных и схему при запуске
- **Supabase**: PostgreSQL хостинг сервис, используемый MISIX

## Requirements

### Requirement 1

**User Story:** Как системный администратор, я хочу чтобы таблица users поддерживала только Telegram-пользователей, чтобы бот мог корректно работать.

#### Acceptance Criteria

1. WHEN the users table schema is updated THEN the email column SHALL be nullable
2. WHEN the users table schema is updated THEN the password_hash column SHALL be nullable
3. WHEN a Telegram user is created THEN the System SHALL allow null values for email and password_hash
4. WHEN a Telegram user is created THEN the System SHALL require non-null telegram_id
5. WHEN the database validator runs THEN the System SHALL successfully create and delete test Telegram users without email credentials

### Requirement 2

**User Story:** As a developer, I want the database migration to be applied safely, so that existing user data is preserved and the application continues functioning.

#### Acceptance Criteria

1. WHEN the migration is applied THEN the System SHALL preserve all existing user records
2. WHEN the migration is applied THEN the System SHALL maintain all foreign key relationships
3. WHEN the migration is applied THEN the System SHALL maintain all indexes on the users table
4. WHEN the migration completes THEN the System SHALL verify the schema changes were applied correctly

### Requirement 3

**User Story:** As a system operator, I want clear instructions for applying the database fix, so that I can resolve the issue quickly in production.

#### Acceptance Criteria

1. WHEN the migration SQL is provided THEN it SHALL include ALTER TABLE statements to modify column constraints
2. WHEN the migration SQL is provided THEN it SHALL be idempotent and safe to run multiple times
3. WHEN applying the fix THEN the System SHALL provide a Python script for automated application via Supabase client
4. WHEN the fix is applied THEN the System SHALL log success or failure clearly
