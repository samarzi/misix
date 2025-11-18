-- QUICK FIX для таблицы users
-- Скопируйте и вставьте в Supabase SQL Editor

-- Шаг 1: Добавить колонки (если их нет)
ALTER TABLE users ADD COLUMN IF NOT EXISTS email TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS first_name TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_name TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name TEXT;

-- Шаг 2: Заполнить существующие записи
UPDATE users 
SET 
    email = COALESCE(email, 'user_' || id || '@misix.local'),
    password_hash = COALESCE(password_hash, '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIxF6k0O3i'),
    first_name = COALESCE(first_name, username, 'User'),
    last_name = COALESCE(last_name, ''),
    full_name = COALESCE(full_name, username, 'User ' || id)
WHERE email IS NULL OR password_hash IS NULL OR first_name IS NULL;

-- Шаг 3: Сделать обязательными
ALTER TABLE users ALTER COLUMN email SET NOT NULL;
ALTER TABLE users ALTER COLUMN password_hash SET NOT NULL;
ALTER TABLE users ALTER COLUMN first_name SET NOT NULL;

-- Шаг 4: Добавить unique constraint на email
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_unique ON users(email);

-- Готово!
SELECT 'Users table fixed!' as status;
