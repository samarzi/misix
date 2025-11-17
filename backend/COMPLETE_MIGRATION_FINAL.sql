-- ============================================================================
-- MISIX COMPLETE DATABASE MIGRATION
-- ============================================================================
-- Этот файл содержит ВСЕ необходимые миграции для полной настройки БД
-- Применяйте в правильной базе данных Supabase
-- 
-- Инструкции:
-- 1. Откройте https://supabase.com/dashboard
-- 2. Выберите ПРАВИЛЬНЫЙ проект (dcxdnrealygulikpuicm)
-- 3. Перейдите в SQL Editor
-- 4. Скопируйте и вставьте весь этот файл
-- 5. Нажмите "Run"
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Trigger function for updating updated_at timestamp
CREATE OR REPLACE FUNCTION trigger_set_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- TABLE: users
-- ============================================================================

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    telegram_id BIGINT UNIQUE,
    username TEXT,
    first_name TEXT NOT NULL,
    last_name TEXT,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    avatar_url TEXT,
    bio TEXT,
    email_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Add missing columns if table already exists
DO $$ 
BEGIN
    ALTER TABLE users ADD COLUMN IF NOT EXISTS first_name TEXT;
    ALTER TABLE users ADD COLUMN IF NOT EXISTS last_name TEXT;
    ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name TEXT;
    ALTER TABLE users ADD COLUMN IF NOT EXISTS email TEXT;
    ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash TEXT;
    ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url TEXT;
    ALTER TABLE users ADD COLUMN IF NOT EXISTS bio TEXT;
    ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE;
END $$;

-- Update existing users with default values
UPDATE users 
SET 
    first_name = COALESCE(first_name, username, 'User'),
    last_name = COALESCE(last_name, ''),
    full_name = COALESCE(full_name, username, CONCAT('User ', id)),
    email = COALESCE(email, CONCAT('user_', id, '@misix.local')),
    password_hash = COALESCE(password_hash, '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIxF6k0O3i')
WHERE first_name IS NULL OR email IS NULL OR password_hash IS NULL OR full_name IS NULL;

-- Make required columns NOT NULL
ALTER TABLE users 
ALTER COLUMN first_name SET NOT NULL,
ALTER COLUMN full_name SET NOT NULL,
ALTER COLUMN email SET NOT NULL,
ALTER COLUMN password_hash SET NOT NULL;

-- Indexes
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at DESC);

-- Trigger
DROP TRIGGER IF EXISTS set_users_updated_at ON users;
CREATE TRIGGER set_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE PROCEDURE trigger_set_timestamp();

-- ============================================================================
-- TABLE: tasks
-- ============================================================================

CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    telegram_id BIGINT,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'cancelled')),
    priority TEXT DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high')),
    deadline TIMESTAMPTZ,
    last_reminder_sent_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT tasks_user_fk FOREIGN KEY (user_id)
        REFERENCES users (id) ON DELETE CASCADE
);

-- Add missing columns if table already exists
DO $$ 
BEGIN
    ALTER TABLE tasks ADD COLUMN IF NOT EXISTS last_reminder_sent_at TIMESTAMPTZ;
END $$;

-- Indexes
CREATE INDEX IF NOT EXISTS idx_tasks_user ON tasks (user_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks (user_id, status);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks (user_id, priority);
CREATE INDEX IF NOT EXISTS idx_tasks_deadline ON tasks (user_id, deadline DESC);
CREATE INDEX IF NOT EXISTS idx_tasks_deadline_active ON tasks(deadline) 
    WHERE status != 'completed' AND deadline IS NOT NULL;

-- Trigger
DROP TRIGGER IF EXISTS set_tasks_updated_at ON tasks;
CREATE TRIGGER set_tasks_updated_at
    BEFORE UPDATE ON tasks
    FOR EACH ROW
    EXECUTE PROCEDURE trigger_set_timestamp();

-- ============================================================================
-- TABLE: finance_entries
-- ============================================================================

CREATE TABLE IF NOT EXISTS finance_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    telegram_id BIGINT,
    type TEXT NOT NULL CHECK (type IN ('income', 'expense')),
    amount DECIMAL(12,2) NOT NULL CHECK (amount > 0),
    category TEXT NOT NULL,
    description TEXT,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT finance_entries_user_fk FOREIGN KEY (user_id)
        REFERENCES users (id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_finance_user ON finance_entries (user_id);
CREATE INDEX IF NOT EXISTS idx_finance_date ON finance_entries (user_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_finance_type ON finance_entries (user_id, type);
CREATE INDEX IF NOT EXISTS idx_finance_category ON finance_entries (user_id, category);

-- Trigger
DROP TRIGGER IF EXISTS set_finance_entries_updated_at ON finance_entries;
CREATE TRIGGER set_finance_entries_updated_at
    BEFORE UPDATE ON finance_entries
    FOR EACH ROW
    EXECUTE PROCEDURE trigger_set_timestamp();

-- ============================================================================
-- TABLE: note_folders
-- ============================================================================

CREATE TABLE IF NOT EXISTS note_folders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    name TEXT NOT NULL,
    parent_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT note_folders_user_fk FOREIGN KEY (user_id)
        REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT note_folders_parent_fk FOREIGN KEY (parent_id)
        REFERENCES note_folders (id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_note_folders_user ON note_folders (user_id);
CREATE INDEX IF NOT EXISTS idx_note_folders_parent ON note_folders (parent_id);

-- Trigger
DROP TRIGGER IF EXISTS set_note_folders_updated_at ON note_folders;
CREATE TRIGGER set_note_folders_updated_at
    BEFORE UPDATE ON note_folders
    FOR EACH ROW
    EXECUTE PROCEDURE trigger_set_timestamp();

-- ============================================================================
-- TABLE: notes
-- ============================================================================

CREATE TABLE IF NOT EXISTS notes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    telegram_id BIGINT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    folder_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT notes_user_fk FOREIGN KEY (user_id)
        REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT notes_folder_fk FOREIGN KEY (folder_id)
        REFERENCES note_folders (id) ON DELETE SET NULL
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_notes_user ON notes (user_id);
CREATE INDEX IF NOT EXISTS idx_notes_folder ON notes (folder_id);
CREATE INDEX IF NOT EXISTS idx_notes_created_at ON notes (user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notes_updated_at ON notes (user_id, updated_at DESC);

-- Trigger
DROP TRIGGER IF EXISTS set_notes_updated_at ON notes;
CREATE TRIGGER set_notes_updated_at
    BEFORE UPDATE ON notes
    FOR EACH ROW
    EXECUTE PROCEDURE trigger_set_timestamp();

-- ============================================================================
-- TABLE: mood_entries
-- ============================================================================

CREATE TABLE IF NOT EXISTS mood_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    telegram_id BIGINT,
    mood TEXT NOT NULL CHECK (mood IN ('happy', 'sad', 'anxious', 'calm', 'excited', 'tired', 'stressed', 'angry', 'neutral')),
    intensity INTEGER NOT NULL CHECK (intensity >= 1 AND intensity <= 10),
    note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT mood_entries_user_fk FOREIGN KEY (user_id)
        REFERENCES users (id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_mood_user ON mood_entries (user_id);
CREATE INDEX IF NOT EXISTS idx_mood_created_at ON mood_entries (user_id, created_at DESC);

-- Trigger
DROP TRIGGER IF EXISTS set_mood_entries_updated_at ON mood_entries;
CREATE TRIGGER set_mood_entries_updated_at
    BEFORE UPDATE ON mood_entries
    FOR EACH ROW
    EXECUTE PROCEDURE trigger_set_timestamp();

-- ============================================================================
-- TABLE: assistant_messages
-- ============================================================================

CREATE TABLE IF NOT EXISTS assistant_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    telegram_id BIGINT,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT assistant_messages_user_fk FOREIGN KEY (user_id)
        REFERENCES users (id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_assistant_messages_user ON assistant_messages (user_id);
CREATE INDEX IF NOT EXISTS idx_assistant_messages_created_at ON assistant_messages (user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_assistant_messages_role ON assistant_messages (user_id, role);

-- ============================================================================
-- TABLE: user_settings
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL UNIQUE,
    reminders_enabled BOOLEAN DEFAULT TRUE,
    daily_summary_time TIME DEFAULT '09:00:00',
    reminder_minutes_before INTEGER DEFAULT 60,
    timezone TEXT DEFAULT 'UTC',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT user_settings_user_fk FOREIGN KEY (user_id)
        REFERENCES users (id) ON DELETE CASCADE
);

-- Indexes
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_settings_user ON user_settings (user_id);

-- Trigger
DROP TRIGGER IF EXISTS set_user_settings_updated_at ON user_settings;
CREATE TRIGGER set_user_settings_updated_at
    BEFORE UPDATE ON user_settings
    FOR EACH ROW
    EXECUTE PROCEDURE trigger_set_timestamp();

-- ============================================================================
-- TABLE: sleep_tracking
-- ============================================================================

CREATE TABLE IF NOT EXISTS sleep_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    telegram_id BIGINT,
    sleep_start TIMESTAMPTZ NOT NULL,
    sleep_end TIMESTAMPTZ,
    sleep_date DATE NOT NULL,
    duration_minutes INTEGER,
    quality TEXT CHECK (quality IN ('poor', 'fair', 'good', 'excellent')),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT sleep_tracking_user_fk FOREIGN KEY (user_id)
        REFERENCES users (id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_sleep_user ON sleep_tracking (user_id);
CREATE INDEX IF NOT EXISTS idx_sleep_date ON sleep_tracking (user_id, sleep_date DESC);
CREATE INDEX IF NOT EXISTS idx_sleep_start ON sleep_tracking (user_id, sleep_start DESC);

-- Trigger
DROP TRIGGER IF EXISTS set_sleep_tracking_updated_at ON sleep_tracking;
CREATE TRIGGER set_sleep_tracking_updated_at
    BEFORE UPDATE ON sleep_tracking
    FOR EACH ROW
    EXECUTE PROCEDURE trigger_set_timestamp();

-- ============================================================================
-- TABLE: personal_entries
-- ============================================================================

CREATE TABLE IF NOT EXISTS personal_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    telegram_id BIGINT,
    entry_type TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT personal_entries_user_fk FOREIGN KEY (user_id)
        REFERENCES users (id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_personal_user ON personal_entries (user_id);
CREATE INDEX IF NOT EXISTS idx_personal_type ON personal_entries (user_id, entry_type);
CREATE INDEX IF NOT EXISTS idx_personal_created_at ON personal_entries (user_id, created_at DESC);

-- Trigger
DROP TRIGGER IF EXISTS set_personal_entries_updated_at ON personal_entries;
CREATE TRIGGER set_personal_entries_updated_at
    BEFORE UPDATE ON personal_entries
    FOR EACH ROW
    EXECUTE PROCEDURE trigger_set_timestamp();

-- ============================================================================
-- VERIFICATION
-- ============================================================================

DO $$
DECLARE
    table_count INTEGER;
    required_tables TEXT[] := ARRAY[
        'users', 'tasks', 'finance_entries', 'notes', 'note_folders',
        'mood_entries', 'assistant_messages', 'user_settings',
        'sleep_tracking', 'personal_entries'
    ];
    tbl TEXT;
    missing_tables TEXT[] := ARRAY[]::TEXT[];
BEGIN
    -- Check all required tables exist
    FOREACH tbl IN ARRAY required_tables
    LOOP
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_name = tbl AND table_schema = 'public'
        ) THEN
            missing_tables := array_append(missing_tables, tbl);
        END IF;
    END LOOP;
    
    table_count := array_length(required_tables, 1) - array_length(missing_tables, 1);
    
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'MIGRATION VERIFICATION';
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'Required tables: %', array_length(required_tables, 1);
    RAISE NOTICE 'Found tables: %', table_count;
    
    IF array_length(missing_tables, 1) > 0 THEN
        RAISE WARNING 'Missing tables: %', array_to_string(missing_tables, ', ');
    ELSE
        RAISE NOTICE '✅ All required tables exist!';
    END IF;
    
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'Migration completed successfully!';
    RAISE NOTICE 'Run: python3 diagnose.py to verify system health';
    RAISE NOTICE '============================================================';
END $$;

-- Show table summary
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN (
    'users', 'tasks', 'finance_entries', 'notes', 'note_folders',
    'mood_entries', 'assistant_messages', 'user_settings',
    'sleep_tracking', 'personal_entries'
)
ORDER BY tablename;
