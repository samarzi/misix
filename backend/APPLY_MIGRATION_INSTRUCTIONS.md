# Инструкция по применению миграции 009_remove_email_auth

## Проблема

Таблица `users` требует поля `email` и `password_hash`, но приложение использует только Telegram-аутентификацию через `telegram_id`.

## Решение

Применить миграцию `migrations/009_remove_email_auth.sql`, которая:
- Удаляет колонки `email`, `password_hash`, `email_verified`
- Делает `telegram_id` обязательным (NOT NULL)
- Удаляет индекс на `email`

## Способы применения

### Способ 1: Supabase SQL Editor (Рекомендуется)

1. Откройте Supabase Dashboard: https://app.supabase.com
2. Выберите ваш проект
3. Перейдите в SQL Editor (левое меню)
4. Создайте новый query
5. Скопируйте содержимое файла `migrations/009_remove_email_auth.sql`
6. Вставьте в SQL Editor
7. Нажмите "Run" или Ctrl+Enter
8. Проверьте результат - должны появиться сообщения об успешном выполнении

### Способ 2: psql Command Line

Если у вас есть доступ к PostgreSQL через psql:

```bash
# Получите connection string из Supabase Dashboard:
# Settings -> Database -> Connection string -> URI

psql "postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-ID].supabase.co:5432/postgres" \
  -f migrations/009_remove_email_auth.sql
```

### Способ 3: Python скрипт (требует psycopg2)

```bash
# Установите psycopg2 если еще не установлен
pip install psycopg2-binary

# Установите переменную окружения с паролем БД
export SUPABASE_DB_PASSWORD='your_database_password'

# Запустите скрипт
python apply_migration_direct.py
```

## Проверка результата

После применения миграции проверьте схему:

```sql
-- Проверить колонки таблицы users
SELECT column_name, is_nullable, data_type
FROM information_schema.columns
WHERE table_name = 'users'
ORDER BY ordinal_position;
```

Должны отсутствовать:
- `email`
- `password_hash`
- `email_verified`

Колонка `telegram_id` должна быть `NOT NULL`.

## Тестирование

После применения миграции:

1. Перезапустите приложение
2. Проверьте логи - не должно быть ошибок валидации БД
3. Отправьте сообщение боту в Telegram
4. Проверьте, что бот отвечает
5. Проверьте, что новый пользователь создался в БД

## Откат (если нужно)

Если нужно откатить изменения:

```sql
-- Добавить обратно колонки (НЕ РЕКОМЕНДУЕТСЯ)
ALTER TABLE users ADD COLUMN email text unique;
ALTER TABLE users ADD COLUMN password_hash text;
ALTER TABLE users ADD COLUMN email_verified boolean default false;
ALTER TABLE users ALTER COLUMN telegram_id DROP NOT NULL;
CREATE INDEX idx_users_email ON users (email);
```

**Внимание**: Откат не рекомендуется, так как приложение не использует email-аутентификацию.

## SQL миграция

Файл: `migrations/009_remove_email_auth.sql`

```sql
-- Migration: Remove email authentication from users table
-- Description: Remove email, password_hash, and email_verified columns
--              Make telegram_id NOT NULL as it's the only authentication method
-- Date: 2025-11-18

-- Start transaction
BEGIN;

-- Drop index on email if it exists
DROP INDEX IF EXISTS idx_users_email;

-- Drop email_verified column if it exists
ALTER TABLE users DROP COLUMN IF EXISTS email_verified;

-- Drop password_hash column if it exists
ALTER TABLE users DROP COLUMN IF EXISTS password_hash;

-- Drop email column if it exists (must be last due to unique constraint)
ALTER TABLE users DROP COLUMN IF EXISTS email;

-- Make telegram_id NOT NULL (required for all users)
-- First check if there are any NULL values
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM users WHERE telegram_id IS NULL) THEN
        RAISE EXCEPTION 'Cannot make telegram_id NOT NULL: found users with NULL telegram_id. Please fix data first.';
    END IF;
END $$;

-- Set telegram_id to NOT NULL
ALTER TABLE users ALTER COLUMN telegram_id SET NOT NULL;

-- Ensure telegram_id index exists and is unique
DROP INDEX IF EXISTS idx_users_telegram_id;
CREATE UNIQUE INDEX idx_users_telegram_id ON users (telegram_id);

-- Commit transaction
COMMIT;
```
