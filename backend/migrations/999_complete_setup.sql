-- COMPLETE DATABASE SETUP
-- This migration creates ALL tables needed for MISIX
-- Safe to run multiple times (uses IF NOT EXISTS)

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create timestamp trigger function
CREATE OR REPLACE FUNCTION trigger_set_timestamp()
RETURNS TRIGGER AS $trigger_func$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$trigger_func$ LANGUAGE plpgsql;

-- ============================================================================
-- USERS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    telegram_id BIGINT UNIQUE,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    language_code TEXT,
    email TEXT,
    password_hash TEXT,
    full_name TEXT,
    avatar_url TEXT,
    bio TEXT,
    email_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DROP TRIGGER IF EXISTS set_users_updated_at ON users;
CREATE TRIGGER set_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE PROCEDURE trigger_set_timestamp();

CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users (telegram_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);

-- ============================================================================
-- PROJECTS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    color TEXT,
    deadline TIMESTAMPTZ,
    status TEXT DEFAULT 'active',
    progress_percent INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT projects_user_fk FOREIGN KEY (user_id)
        REFERENCES users (id) ON DELETE CASCADE
);

DROP TRIGGER IF EXISTS set_projects_updated_at ON projects;
CREATE TRIGGER set_projects_updated_at
    BEFORE UPDATE ON projects
    FOR EACH ROW
    EXECUTE PROCEDURE trigger_set_timestamp();

CREATE INDEX IF NOT EXISTS idx_projects_user ON projects (user_id);

-- ============================================================================
-- TASKS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    project_id UUID,
    telegram_id BIGINT,
    title TEXT NOT NULL,
    description TEXT,
    priority TEXT DEFAULT 'medium',
    status TEXT DEFAULT 'new',
    deadline TIMESTAMPTZ,
    last_reminder_sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT tasks_user_fk FOREIGN KEY (user_id)
        REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT tasks_project_fk FOREIGN KEY (project_id)
        REFERENCES projects (id) ON DELETE SET NULL
);

DROP TRIGGER IF EXISTS set_tasks_updated_at ON tasks;
CREATE TRIGGER set_tasks_updated_at
    BEFORE UPDATE ON tasks
    FOR EACH ROW
    EXECUTE PROCEDURE trigger_set_timestamp();

CREATE INDEX IF NOT EXISTS idx_tasks_user ON tasks (user_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks (user_id, status);
CREATE INDEX IF NOT EXISTS idx_tasks_deadline ON tasks (deadline) WHERE status != 'completed' AND deadline IS NOT NULL;

-- ============================================================================
-- FINANCE_ENTRIES TABLE
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

DROP TRIGGER IF EXISTS set_finance_entries_updated_at ON finance_entries;
CREATE TRIGGER set_finance_entries_updated_at
    BEFORE UPDATE ON finance_entries
    FOR EACH ROW
    EXECUTE PROCEDURE trigger_set_timestamp();

CREATE INDEX IF NOT EXISTS idx_finance_user ON finance_entries (user_id);
CREATE INDEX IF NOT EXISTS idx_finance_date ON finance_entries (user_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_finance_type ON finance_entries (user_id, type);

-- ============================================================================
-- NOTES TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS notes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    telegram_id BIGINT,
    title TEXT,
    content TEXT NOT NULL,
    is_favorite BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT notes_user_fk FOREIGN KEY (user_id)
        REFERENCES users (id) ON DELETE CASCADE
);

DROP TRIGGER IF EXISTS set_notes_updated_at ON notes;
CREATE TRIGGER set_notes_updated_at
    BEFORE UPDATE ON notes
    FOR EACH ROW
    EXECUTE PROCEDURE trigger_set_timestamp();

CREATE INDEX IF NOT EXISTS idx_notes_user ON notes (user_id);
CREATE INDEX IF NOT EXISTS idx_notes_created ON notes (user_id, created_at DESC);

-- ============================================================================
-- PERSONAL_ENTRIES TABLE
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

DROP TRIGGER IF EXISTS set_personal_entries_updated_at ON personal_entries;
CREATE TRIGGER set_personal_entries_updated_at
    BEFORE UPDATE ON personal_entries
    FOR EACH ROW
    EXECUTE PROCEDURE trigger_set_timestamp();

CREATE INDEX IF NOT EXISTS idx_personal_user ON personal_entries (user_id);
CREATE INDEX IF NOT EXISTS idx_personal_type ON personal_entries (user_id, entry_type);

-- ============================================================================
-- MOOD_ENTRIES TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS mood_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    telegram_id BIGINT,
    mood TEXT NOT NULL,
    intensity INTEGER CHECK (intensity >= 1 AND intensity <= 10),
    note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT mood_entries_user_fk FOREIGN KEY (user_id)
        REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_mood_user ON mood_entries (user_id);
CREATE INDEX IF NOT EXISTS idx_mood_created ON mood_entries (user_id, created_at DESC);

-- ============================================================================
-- SLEEP_TRACKING TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS sleep_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    telegram_id BIGINT,
    sleep_start TIMESTAMPTZ NOT NULL,
    sleep_end TIMESTAMPTZ,
    sleep_date DATE NOT NULL,
    duration_minutes INTEGER,
    quality TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT sleep_tracking_user_fk FOREIGN KEY (user_id)
        REFERENCES users (id) ON DELETE CASCADE
);

DROP TRIGGER IF EXISTS set_sleep_tracking_updated_at ON sleep_tracking;
CREATE TRIGGER set_sleep_tracking_updated_at
    BEFORE UPDATE ON sleep_tracking
    FOR EACH ROW
    EXECUTE PROCEDURE trigger_set_timestamp();

CREATE INDEX IF NOT EXISTS idx_sleep_user ON sleep_tracking (user_id);
CREATE INDEX IF NOT EXISTS idx_sleep_date ON sleep_tracking (user_id, sleep_date DESC);

-- ============================================================================
-- USER_SETTINGS TABLE (for reminders)
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_settings (
    user_id UUID PRIMARY KEY,
    reminders_enabled BOOLEAN DEFAULT TRUE,
    daily_summary_time TIME DEFAULT '09:00',
    reminder_minutes_before INTEGER DEFAULT 60,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT user_settings_user_fk FOREIGN KEY (user_id)
        REFERENCES users (id) ON DELETE CASCADE
);

DROP TRIGGER IF EXISTS set_user_settings_updated_at ON user_settings;
CREATE TRIGGER set_user_settings_updated_at
    BEFORE UPDATE ON user_settings
    FOR EACH ROW
    EXECUTE PROCEDURE trigger_set_timestamp();

CREATE INDEX IF NOT EXISTS idx_user_settings_reminders ON user_settings (reminders_enabled) WHERE reminders_enabled = TRUE;

-- ============================================================================
-- TAGS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS tags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    name TEXT NOT NULL,
    color TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT tags_user_fk FOREIGN KEY (user_id)
        REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT tags_user_name_unique UNIQUE (user_id, name)
);

CREATE INDEX IF NOT EXISTS idx_tags_user ON tags (user_id);

-- ============================================================================
-- VERIFY SETUP
-- ============================================================================

DO $$
DECLARE
    table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_type = 'BASE TABLE';
    
    RAISE NOTICE '✅ Database setup complete!';
    RAISE NOTICE '📊 Total tables: %', table_count;
    RAISE NOTICE '🎉 MISIX is ready to use!';
END $$;
