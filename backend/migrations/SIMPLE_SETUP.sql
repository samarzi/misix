-- SIMPLE DATABASE SETUP FOR MISIX
-- Copy and paste this entire file into Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

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

CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users (telegram_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);

-- ============================================================================
-- PROJECTS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    color TEXT,
    deadline TIMESTAMPTZ,
    status TEXT DEFAULT 'active',
    progress_percent INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_projects_user ON projects (user_id);

-- ============================================================================
-- TASKS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    telegram_id BIGINT,
    title TEXT NOT NULL,
    description TEXT,
    priority TEXT DEFAULT 'medium',
    status TEXT DEFAULT 'new',
    deadline TIMESTAMPTZ,
    last_reminder_sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tasks_user ON tasks (user_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks (user_id, status);
CREATE INDEX IF NOT EXISTS idx_tasks_deadline ON tasks (deadline) WHERE status != 'completed' AND deadline IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_tasks_user_created ON tasks (user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tasks_user_priority ON tasks (user_id, priority);

-- ============================================================================
-- FINANCE_ENTRIES TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS finance_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    telegram_id BIGINT,
    type TEXT NOT NULL CHECK (type IN ('income', 'expense')),
    amount DECIMAL(12,2) NOT NULL CHECK (amount > 0),
    category TEXT NOT NULL,
    description TEXT,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_finance_user ON finance_entries (user_id);
CREATE INDEX IF NOT EXISTS idx_finance_date ON finance_entries (user_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_finance_type ON finance_entries (user_id, type);
CREATE INDEX IF NOT EXISTS idx_finance_user_category ON finance_entries (user_id, category);

-- ============================================================================
-- NOTES TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS notes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    telegram_id BIGINT,
    title TEXT,
    content TEXT NOT NULL,
    is_favorite BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notes_user ON notes (user_id);
CREATE INDEX IF NOT EXISTS idx_notes_created ON notes (user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notes_updated ON notes (user_id, updated_at DESC);

-- ============================================================================
-- PERSONAL_ENTRIES TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS personal_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    telegram_id BIGINT,
    entry_type TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_personal_user ON personal_entries (user_id);
CREATE INDEX IF NOT EXISTS idx_personal_type ON personal_entries (user_id, entry_type);
CREATE INDEX IF NOT EXISTS idx_personal_created ON personal_entries (user_id, created_at DESC);

-- ============================================================================
-- MOOD_ENTRIES TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS mood_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    telegram_id BIGINT,
    mood TEXT NOT NULL,
    intensity INTEGER CHECK (intensity >= 1 AND intensity <= 10),
    note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_mood_user ON mood_entries (user_id);
CREATE INDEX IF NOT EXISTS idx_mood_created ON mood_entries (user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_mood_user_mood ON mood_entries (user_id, mood);

-- ============================================================================
-- SLEEP_TRACKING TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS sleep_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    telegram_id BIGINT,
    sleep_start TIMESTAMPTZ NOT NULL,
    sleep_end TIMESTAMPTZ,
    sleep_date DATE NOT NULL,
    duration_minutes INTEGER,
    quality TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sleep_user ON sleep_tracking (user_id);
CREATE INDEX IF NOT EXISTS idx_sleep_date ON sleep_tracking (user_id, sleep_date DESC);
CREATE INDEX IF NOT EXISTS idx_sleep_start ON sleep_tracking (user_id, sleep_start DESC);

-- ============================================================================
-- USER_SETTINGS TABLE (for reminders)
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_settings (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    reminders_enabled BOOLEAN DEFAULT TRUE,
    daily_summary_time TIME DEFAULT '09:00',
    reminder_minutes_before INTEGER DEFAULT 60,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_settings_reminders ON user_settings (reminders_enabled) WHERE reminders_enabled = TRUE;

-- ============================================================================
-- TAGS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS tags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    color TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT tags_user_name_unique UNIQUE (user_id, name)
);

CREATE INDEX IF NOT EXISTS idx_tags_user ON tags (user_id);

-- ============================================================================
-- SUCCESS MESSAGE
-- ============================================================================

SELECT 
    'SUCCESS! Database setup complete. Total tables: ' || COUNT(*)::TEXT AS message
FROM information_schema.tables
WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
