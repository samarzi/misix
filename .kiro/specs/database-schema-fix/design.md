# Design Document

## Overview

Этот документ описывает решение критической проблемы схемы базы данных, которая не позволяет боту MISIX корректно работать. Проблема заключается в том, что колонки `email` и `password_hash` в таблице `users` имеют ограничение NOT NULL, но приложение использует только Telegram-аутентификацию через telegram_id и не использует email вообще.

## Architecture

Решение состоит из трех компонентов:

1. **SQL Migration Script** - SQL скрипт для изменения схемы таблицы users
2. **Python Application Script** - Python скрипт для автоматического применения миграции через Supabase client
3. **Validation Updates** - Обновление логики валидации для корректной работы с новой схемой

## Components and Interfaces

### 1. SQL Migration Script

Файл: `backend/migrations/008_fix_users_nullable.sql`

Скрипт выполняет следующие операции:
- Изменяет колонку `email` на nullable
- Изменяет колонку `password_hash` на nullable
- Добавляет CHECK constraint для обеспечения того, что все пользователи имеют telegram_id (обязательное поле)

### 2. Python Application Script

Файл: `backend/apply_schema_fix.py`

Скрипт:
- Читает SQL миграцию из файла
- Подключается к Supabase используя существующие credentials
- Выполняет SQL через Supabase client
- Проверяет успешность применения
- Логирует результаты

### 3. Database Validator Updates

Файл: `backend/app/core/database.py`

Обновления:
- Метод `test_write_operation()` уже корректно создает Telegram-пользователя без email
- После применения миграции тест будет проходить успешно

## Data Models

### Users Table Schema (After Migration)

```sql
create table users (
    id uuid primary key default uuid_generate_v4(),
    email text unique,  -- NULLABLE (was NOT NULL) - не используется
    password_hash text,  -- NULLABLE (was NOT NULL) - не используется
    full_name text not null,
    avatar_url text,
    bio text,
    telegram_id bigint unique not null,  -- ОБЯЗАТЕЛЬНОЕ поле для всех пользователей
    username text,
    language_code text,
    email_verified boolean default false,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Schema modification preserves existing data

*For any* existing user record in the database, after applying the migration, the record should remain unchanged with all field values preserved.

**Validates: Requirements 2.1**

### Property 2: Telegram users can be created without email

*For any* valid Telegram user data (with telegram_id but without email/password), after the migration, the System should successfully insert the user into the database.

**Validates: Requirements 1.3**

### Property 3: All users require telegram_id

*For any* user creation attempt without telegram_id, the System should reject the insertion with a constraint violation.

**Validates: Requirements 1.4**

### Property 4: Database validator test passes

*For any* execution of the database validator's test_write_operation method, after the migration, the test should complete successfully without constraint violations.

**Validates: Requirements 1.5**

### Property 5: Migration is idempotent

*For any* number of times the migration is applied, the final schema state should be identical and no errors should occur.

**Validates: Requirements 3.2**

## Error Handling

### Migration Errors

- **Connection Failure**: Если не удается подключиться к Supabase, скрипт должен вывести четкое сообщение об ошибке с деталями подключения
- **SQL Execution Error**: Если SQL команда не выполняется, скрипт должен вывести полный текст ошибки PostgreSQL
- **Constraint Violation**: Если существующие данные нарушают новые constraints, миграция должна откатиться

### Runtime Errors

- **Invalid User Data**: При попытке создать пользователя без telegram_id и без email/password, должна возвращаться ошибка валидации
- **Duplicate Telegram ID**: При попытке создать пользователя с существующим telegram_id, должна возвращаться ошибка уникальности

## Testing Strategy

### Unit Tests

Тесты не требуются для этой миграции, так как это одноразовое изменение схемы.

### Manual Verification

После применения миграции необходимо:

1. Проверить, что колонки email и password_hash nullable:
```sql
SELECT column_name, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'users' 
AND column_name IN ('email', 'password_hash');
```

2. Проверить, что можно создать Telegram-пользователя:
```sql
INSERT INTO users (telegram_id, username, full_name, language_code)
VALUES (123456789, 'test_user', 'Test User', 'en');
```

3. Проверить, что database validator проходит успешно:
```bash
cd backend
python -c "
import asyncio
from app.core.database import DatabaseValidator

async def test():
    validator = DatabaseValidator()
    result = await validator.test_write_operation()
    print(f'Test result: {result}')

asyncio.run(test())
"
```

4. Перезапустить приложение и проверить логи на отсутствие ошибок валидации базы данных

### Integration Testing

После применения миграции:
- Отправить сообщение боту в Telegram
- Проверить, что бот отвечает корректно
- Проверить, что новые пользователи создаются успешно
