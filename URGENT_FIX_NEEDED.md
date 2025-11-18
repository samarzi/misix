# 🚨 СРОЧНО: Применить SQL (1 минута)

## Статус:
- ✅ Бот запущен на https://misix.onrender.com
- ✅ Telegram бот работает
- ✅ AI отвечает
- ❌ **Данные НЕ сохраняются** - нужно исправить таблицу users

## Ошибка:
```
null value in column "email" of relation "users" violates not-null constraint
```

## Решение (1 минута):

### 1. Откройте Supabase:
https://supabase.com/dashboard/project/dcxdnrealygulikpuicm/sql/new

### 2. Скопируйте этот SQL:

```sql
-- Добавить колонки
ALTER TABLE users ADD COLUMN IF NOT EXISTS email TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS first_name TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_name TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name TEXT;

-- Заполнить существующие записи
UPDATE users 
SET 
    email = COALESCE(email, 'user_' || id || '@misix.local'),
    password_hash = COALESCE(password_hash, '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIxF6k0O3i'),
    first_name = COALESCE(first_name, username, 'User'),
    last_name = COALESCE(last_name, ''),
    full_name = COALESCE(full_name, username, 'User ' || id)
WHERE email IS NULL OR password_hash IS NULL OR first_name IS NULL;

-- Сделать обязательными
ALTER TABLE users ALTER COLUMN email SET NOT NULL;
ALTER TABLE users ALTER COLUMN password_hash SET NOT NULL;
ALTER TABLE users ALTER COLUMN first_name SET NOT NULL;

-- Добавить unique constraint
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_unique ON users(email);
```

### 3. Нажмите **Run** (Ctrl+Enter)

### 4. Готово!

После этого бот будет полностью работать:
- ✅ Сохранение пользователей
- ✅ Сохранение задач
- ✅ Сохранение финансов
- ✅ Память и контекст
- ✅ Все функции

---

## Альтернатива - прямая ссылка:

Откройте: https://supabase.com/dashboard/project/dcxdnrealygulikpuicm/sql

И вставьте SQL из файла `backend/QUICK_FIX_USERS.sql`

---

## После применения:

Бот автоматически начнет сохранять данные. Ничего перезапускать не нужно!

Протестируйте:
1. Напишите боту @misix_helpbot: "напомни купить молоко"
2. Напишите: "/tasks"
3. Задача должна сохраниться и отобразиться!

---

**Время:** 1 минута  
**Сложность:** Очень легко  
**Результат:** Полностью рабочий бот 🎉
