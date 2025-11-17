-- ============================================================================
-- MISIX Database Migrations - Apply these in Supabase SQL Editor
-- ============================================================================
-- Instructions:
-- 1. Go to https://supabase.com/dashboard
-- 2. Select your project (dcxdnrealygulikpuicm)
-- 3. Go to SQL Editor
-- 4. Copy and paste this entire file
-- 5. Click "Run"
-- ============================================================================

-- Enable UUID extension if not exists
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create trigger function if not exists
CREATE OR REPLACE FUNCTION trigger_set_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Create FINANCE_ENTRIES table if not exists
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
-- Create PERSONAL_ENTRIES table if not exists
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
-- Create SLEEP_TRACKING table if not exists
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

DROP TRIGGER IF EXISTS set_sleep_tracking_updated_at ON sleep_tracking;
CREATE TRIGGER set_sleep_tracking_updated_at
    BEFORE UPDATE ON sleep_tracking
    FOR EACH ROW
    EXECUTE PROCEDURE trigger_set_timestamp();

CREATE INDEX IF NOT EXISTS idx_sleep_user ON sleep_tracking (user_id);
CREATE INDEX IF NOT EXISTS idx_sleep_date ON sleep_tracking (user_id, sleep_date DESC);

-- ============================================================================
-- Create USER_SETTINGS table if not exists (for reminders)
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

DROP TRIGGER IF EXISTS set_user_settings_updated_at ON user_settings;
CREATE TRIGGER set_user_settings_updated_at
    BEFORE UPDATE ON user_settings
    FOR EACH ROW
    EXECUTE PROCEDURE trigger_set_timestamp();

CREATE INDEX IF NOT EXISTS idx_user_settings_user ON user_settings (user_id);

-- ============================================================================
-- Add reminder fields to tasks table
-- ============================================================================

ALTER TABLE tasks 
ADD COLUMN IF NOT EXISTS last_reminder_sent_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_tasks_deadline_active
ON tasks(deadline) 
WHERE status != 'completed' AND deadline IS NOT NULL;

-- ============================================================================
-- Verify all tables exist
-- ============================================================================

DO $$
DECLARE
    table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name IN (
        'users', 'tasks', 'notes', 'finance_entries',
        'personal_entries', 'mood_entries', 'sleep_tracking',
        'user_settings', 'assistant_messages'
    );
    
    RAISE NOTICE 'Found % out of 9 required tables', table_count;
    
    IF table_count = 9 THEN
        RAISE NOTICE '✅ All required tables exist!';
    ELSE
        RAISE WARNING '⚠️  Some tables are missing. Expected 9, found %', table_count;
    END IF;
END $$;

-- ============================================================================
-- Done!
-- ============================================================================

SELECT 'Migration completed! Run python3 diagnose.py to verify.' AS status;
