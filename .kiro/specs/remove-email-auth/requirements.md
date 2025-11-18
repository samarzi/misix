# Requirements Document

## Introduction

Приложение MISIX использует только Telegram-аутентификацию через telegram_id. Необходимо полностью удалить всю инфраструктуру email-аутентификации из проекта, включая схему базы данных, API endpoints, сервисы, модели и frontend компоненты.

## Glossary

- **System**: Backend и frontend приложения MISIX
- **Email Authentication**: Система аутентификации через email и password
- **Telegram Authentication**: Система аутентификации через Telegram bot используя telegram_id
- **Users Table**: PostgreSQL таблица для хранения информации о пользователях
- **Auth API**: REST API endpoints для аутентификации
- **Auth Service**: Backend сервис для обработки аутентификации

## Requirements

### Requirement 1

**User Story:** Как системный администратор, я хочу удалить email/password колонки из таблицы users, чтобы схема базы данных соответствовала только Telegram-аутентификации.

#### Acceptance Criteria

1. WHEN the database migration is applied THEN the email column SHALL be removed from users table
2. WHEN the database migration is applied THEN the password_hash column SHALL be removed from users table
3. WHEN the database migration is applied THEN the email_verified column SHALL be removed from users table
4. WHEN the database migration is applied THEN the telegram_id column SHALL be NOT NULL
5. WHEN the database migration is applied THEN all existing user data SHALL be preserved

### Requirement 2

**User Story:** Как разработчик, я хочу удалить все backend компоненты email-аутентификации, чтобы код был чистым и поддерживал только Telegram.

#### Acceptance Criteria

1. WHEN backend code is updated THEN the auth router SHALL be removed or simplified to Telegram-only
2. WHEN backend code is updated THEN the auth service SHALL be removed or simplified to Telegram-only
3. WHEN backend code is updated THEN the auth models SHALL be removed or simplified to Telegram-only
4. WHEN backend code is updated THEN the security module SHALL be simplified to remove password hashing
5. WHEN backend code is updated THEN all API dependencies SHALL be updated to remove email auth checks

### Requirement 3

**User Story:** Как разработчик, я хочу удалить все frontend компоненты email-аутентификации, чтобы пользователи не видели неиспользуемые формы входа.

#### Acceptance Criteria

1. WHEN frontend code is updated THEN email login forms SHALL be removed
2. WHEN frontend code is updated THEN email registration forms SHALL be removed
3. WHEN frontend code is updated THEN password reset flows SHALL be removed
4. WHEN frontend code is updated THEN auth store SHALL be simplified to Telegram-only
5. WHEN frontend code is updated THEN validation schemas SHALL remove email/password fields

### Requirement 4

**User Story:** Как разработчик, я хочу обновить документацию, чтобы она отражала только Telegram-аутентификацию.

#### Acceptance Criteria

1. WHEN documentation is updated THEN authentication docs SHALL describe only Telegram flow
2. WHEN documentation is updated THEN API docs SHALL remove email auth endpoints
3. WHEN documentation is updated THEN environment variable examples SHALL remove email-related vars
4. WHEN documentation is updated THEN README SHALL describe Telegram-only setup

### Requirement 5

**User Story:** Как системный оператор, я хочу чтобы database validator работал корректно после удаления email полей.

#### Acceptance Criteria

1. WHEN database validator runs THEN it SHALL successfully create test Telegram users
2. WHEN database validator runs THEN it SHALL not attempt to use email fields
3. WHEN application starts THEN database validation SHALL pass without errors
4. WHEN bot receives messages THEN users SHALL be created with only telegram_id
