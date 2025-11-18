# Design Document

## Overview

Этот документ описывает полное удаление email-аутентификации из проекта MISIX. Приложение будет использовать только Telegram-аутентификацию через telegram_id. Решение включает изменения в базе данных, backend API, frontend компонентах и документации.

## Architecture

Решение состоит из пяти основных компонентов:

1. **Database Migration** - SQL миграция для удаления email-related колонок
2. **Backend Cleanup** - Удаление/упрощение auth API, сервисов и моделей
3. **Frontend Cleanup** - Удаление форм входа и регистрации
4. **Documentation Updates** - Обновление всей документации
5. **Validator Fixes** - Исправление database validator для работы без email

## Components and Interfaces

### 1. Database Migration

Файл: `backend/migrations/009_remove_email_auth.sql`

Операции:
- DROP COLUMN email
- DROP COLUMN password_hash  
- DROP COLUMN email_verified
- ALTER COLUMN telegram_id SET NOT NULL
- DROP INDEX idx_users_email (если существует)

### 2. Backend Components to Remove/Simplify

#### Auth Router (`backend/app/api/routers/auth.py`)
- Удалить endpoints: `/register`, `/login`, `/reset-password`
- Оставить только Telegram-related endpoints (если есть)
- Или удалить файл полностью, если нет Telegram endpoints

#### Auth Service (`backend/app/services/auth_service.py`)
- Удалить методы: `register_user`, `authenticate_user`, `reset_password`
- Упростить до методов работы с Telegram users
- Или удалить файл полностью

#### Auth Models (`backend/app/models/auth.py`)
- Удалить: `UserRegister`, `UserLogin`, `PasswordReset`
- Оставить только модели для Telegram user data

#### Security Module (`backend/app/core/security.py`)
- Удалить функции хеширования паролей
- Удалить функции верификации паролей
- Оставить только JWT token функции (если используются)

#### API Dependencies (`backend/app/api/deps.py`)
- Упростить `get_current_user` для работы только с Telegram
- Удалить проверки email verification

### 3. Frontend Components to Remove

#### Auth Store (`frontend/src/stores/authStore.ts`)
- Удалить методы: `login`, `register`, `resetPassword`
- Упростить до Telegram-only authentication

#### Validation Schemas (`frontend/src/lib/validation/schemas.ts`)
- Удалить email/password validation schemas

#### Auth Components
- Удалить компоненты форм входа/регистрации (если существуют)
- Удалить компоненты сброса пароля

### 4. Documentation Updates

Файлы для обновления:
- `backend/docs/AUTHENTICATION.md` - описать только Telegram flow
- `backend/.env.example` - удалить email-related переменные
- `README.md` - обновить инструкции по setup
- `backend/README.md` - обновить API документацию

### 5. Database Validator Fix

Файл: `backend/app/core/database.py`

Изменения в методе `test_write_operation()`:
- Убедиться что создается только telegram_id (уже так)
- Удалить любые упоминания email из тестов

## Data Models

### Users Table Schema (After Migration)

```sql
create table users (
    id uuid primary key default uuid_generate_v4(),
    full_name text not null,
    avatar_url text,
    bio text,
    telegram_id bigint unique not null,  -- ОБЯЗАТЕЛЬНОЕ поле
    username text,  -- Telegram username
    language_code text,  -- Telegram language
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index idx_users_telegram_id on users (telegram_id);
```

### User Model (Backend)

```python
class User(BaseModel):
    id: UUID
    full_name: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    telegram_id: int
    username: Optional[str] = None
    language_code: Optional[str] = None
    created_at: datetime
    updated_at: datetime
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Migration preserves user data

*For any* existing user record, after applying the migration, the user's id, telegram_id, full_name and other non-email fields should remain unchanged.

**Validates: Requirements 1.5**

### Property 2: Users require telegram_id

*For any* user creation attempt after migration, the System should require a non-null telegram_id value.

**Validates: Requirements 1.4**

### Property 3: No email endpoints accessible

*For any* HTTP request to removed auth endpoints (/register, /login, /reset-password), the System should return 404 Not Found.

**Validates: Requirements 2.1**

### Property 4: Database validator succeeds

*For any* execution of database validator after changes, the test_write_operation should complete successfully without email-related errors.

**Validates: Requirements 5.1, 5.2, 5.3**

### Property 5: Bot creates users successfully

*For any* new Telegram user interacting with the bot, the System should create a user record with only telegram_id and related Telegram fields.

**Validates: Requirements 5.4**

## Error Handling

### Migration Errors

- **Column Dependencies**: Если есть foreign keys или constraints на email колонки, миграция должна сначала их удалить
- **Data Loss Prevention**: Перед удалением колонок, проверить что они не содержат критичных данных
- **Rollback Plan**: Сохранить backup данных перед миграцией

### Runtime Errors

- **Missing telegram_id**: При попытке создать пользователя без telegram_id, должна возвращаться ошибка валидации
- **Duplicate telegram_id**: При попытке создать пользователя с существующим telegram_id, должна возвращаться ошибка уникальности

### API Errors

- **Removed Endpoints**: Запросы к удаленным endpoints должны возвращать 404 с понятным сообщением
- **Invalid Auth**: Попытки аутентификации без Telegram данных должны возвращать 401 Unauthorized

## Testing Strategy

### Manual Verification

После применения всех изменений:

1. **Database Schema**:
```sql
-- Проверить что email колонки удалены
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'users';

-- Проверить что telegram_id NOT NULL
SELECT column_name, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'users' AND column_name = 'telegram_id';
```

2. **Backend API**:
```bash
# Проверить что email endpoints не доступны
curl -X POST http://localhost:8000/api/auth/register
# Должен вернуть 404

curl -X POST http://localhost:8000/api/auth/login
# Должен вернуть 404
```

3. **Database Validator**:
```bash
cd backend
python -c "
import asyncio
from app.core.database import DatabaseValidator

async def test():
    validator = DatabaseValidator()
    result = await validator.test_write_operation()
    print(f'✅ Test passed: {result}')

asyncio.run(test())
"
```

4. **Bot Functionality**:
- Отправить сообщение боту в Telegram
- Проверить что бот отвечает
- Проверить что новый пользователь создался в БД с telegram_id

5. **Frontend**:
- Открыть frontend приложение
- Убедиться что нет форм входа/регистрации по email
- Проверить что есть только Telegram-related UI (если есть)

### Integration Testing

- Полный flow: новый пользователь → сообщение боту → создание в БД → ответ бота
- Проверка что все CRUD операции с пользователями работают без email полей
- Проверка что приложение стартует без ошибок валидации
