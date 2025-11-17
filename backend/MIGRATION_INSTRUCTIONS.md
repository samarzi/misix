# Database Migration Instructions

## Проблемы
- `relation "tasks" does not exist` - таблица tasks не создана
- `column "email" does not exist` - колонка email отсутствует в users

Это означает, что базовая схема БД не создана или неполная.

## Решение: Применить миграции в правильном порядке

### ⚠️ ВАЖНО: Выберите правильный вариант

**Вариант A: Если БД пустая или можно удалить данные**
- Используйте `000_drop_and_recreate.sql` - полное пересоздание

**Вариант B: Если в БД есть данные которые нужно сохранить**
- Используйте миграции по порядку начиная с 001

### Вариант 1: Через Supabase Dashboard (Рекомендуется)

1. Откройте Supabase Dashboard: https://supabase.com/dashboard
2. Выберите ваш проект
3. Перейдите в SQL Editor
4. Выполните миграции по порядку:

#### Шаг 1: Базовая схема
```sql
-- Скопируйте содержимое файла:
backend/migrations/001_complete_schema.sql
```

#### Шаг 2: Дополнительные колонки
```sql
-- Скопируйте содержимое файла:
backend/migrations/002_add_missing_columns.sql
```

#### Шаг 3: Проверка схемы
```sql
-- Скопируйте содержимое файла:
backend/migrations/003_verify_schema.sql
```

#### Шаг 4: Mood entries
```sql
-- Скопируйте содержимое файла:
backend/migrations/004_add_mood_entries.sql
```

#### Шаг 5: Reminders
```sql
-- Скопируйте содержимое файла:
backend/migrations/005_add_reminders.sql
```

#### Шаг 6: Indexes
```sql
-- Скопируйте содержимое файла:
backend/migrations/006_add_indexes.sql
```

### Вариант 2: Через psql (если есть прямой доступ)

```bash
# Получите DATABASE_URL из Supabase Dashboard -> Settings -> Database

# Примените миграции по порядку
psql $DATABASE_URL -f backend/migrations/001_complete_schema.sql
psql $DATABASE_URL -f backend/migrations/002_add_missing_columns.sql
psql $DATABASE_URL -f backend/migrations/003_verify_schema.sql
psql $DATABASE_URL -f backend/migrations/004_add_mood_entries.sql
psql $DATABASE_URL -f backend/migrations/005_add_reminders.sql
psql $DATABASE_URL -f backend/migrations/006_add_indexes.sql
```

### Вариант 3: Через Supabase CLI

```bash
# Установите Supabase CLI если еще не установлен
npm install -g supabase

# Войдите в аккаунт
supabase login

# Свяжите проект
supabase link --project-ref YOUR_PROJECT_REF

# Примените миграции
supabase db push
```

## Проверка успешного применения

После применения миграций выполните в SQL Editor:

```sql
-- Проверка существования таблиц
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- Должны быть таблицы:
-- - users
-- - tasks
-- - finance_entries
-- - notes
-- - personal_entries
-- - mood_entries
-- - sleep_tracking
-- - user_settings
-- - projects
-- - tags
-- - note_folders
```

## Важные замечания

1. **Порядок важен!** Миграции должны применяться строго по номерам (001, 002, 003...)
2. **Безопасность**: Все миграции используют `IF NOT EXISTS`, поэтому безопасно запускать повторно
3. **Backup**: Supabase автоматически делает backup, но для production рекомендуется сделать ручной backup перед миграцией

## Troubleshooting

### Ошибка: "permission denied"
- Убедитесь что используете правильный DATABASE_URL с правами администратора
- В Supabase Dashboard используйте "Connection pooling" URL для psql

### Ошибка: "already exists"
- Это нормально, миграции используют `IF NOT EXISTS`
- Просто продолжайте со следующей миграцией

### Ошибка: "foreign key constraint"
- Убедитесь что применяете миграции по порядку
- Таблица users должна быть создана первой

## После успешного применения

1. Перезапустите backend сервер
2. Проверьте логи на наличие ошибок БД
3. Протестируйте основные функции (создание задачи, финансы, etc.)

## Контакты для помощи

Если возникли проблемы:
1. Проверьте логи Supabase в Dashboard -> Logs
2. Проверьте переменные окружения в `.env`
3. Убедитесь что `SUPABASE_URL` и `SUPABASE_KEY` корректны
