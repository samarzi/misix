-- Migration: Fix missing tables and columns
-- Description: Safely add missing tables that may not exist in current schema
-- This migration is safe to run multiple times

-- Enable UUID extension if not exists
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create trigger function if not exists
CREATE OR REPLACE FUNCTION trigger_set_timestamp()
RETURNS TRIGGER AS $
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$ LANGUAGE plpgsql;

-- ============================================================================
-- Fix USERS table - add missing columns if they don't exist
-- ============================================================================

DO $$ 
BEGIN
    -- Add email column if missing
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'email'
    ) THEN
        ALTER TABLE users ADD COLUMN email TEXT;
        -- Set default email for existing users
        UPDATE users SET email = CONCAT('user_', id, '@misix.local') WHERE email IS NULL;
        ALTER TABLE users ALTER COLUMN email SET NOT NULL;
        CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_unique ON users(email);
    END IF;

    -- Add password_hash column if missing
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'password_hash'
    ) THEN
        ALTER TABLE users ADD COLUMN password_hash TEXT;
        -- Set default password hash for existing users (they'll need to reset)
        UPDATE users SET password_hash = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIxF6k0O3i' WHERE password_hash IS NULL;
        ALTER TABLE users ALTER COLUMN password_hash SET NOT NULL;
    END IF;

    -- Add full_name column if missing
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'full_name'
    ) THEN
        ALTER TABLE users ADD COLUMN full_name TEXT;
        -- Set default from username or telegram data
        UPDATE users SET full_name = COALESCE(username, CONCAT('User ', id)) WHERE full_name IS NULL;
        ALTER TABLE users ALTER COLUMN full_name SET NOT NULL;
    END IF;

    -- Add other optional columns
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'avatar_url'
    ) THEN
        ALTER TABLE users ADD COLUMN avatar_url TEXT;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'bio'
    ) THEN
        ALTER TABLE users ADD COLUMN bio TEXT;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'email_verified'
    ) THEN
        ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT FALSE;
    END IF;
END $$;

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
-- Verify all critical tables exist
-- ============================================================================

DO $$
DECLARE
    missing_tables TEXT[];
    required_tables TEXT[] := ARRAY[
        'users', 'tasks', 'notes', 'finance_entries', 
        'personal_entries', 'mood_entries', 'sleep_tracking',
        'user_settings', 'projects', 'tags'
    ];
    tbl TEXT;
BEGIN
    missing_tables := ARRAY[]::TEXT[];
    
    FOREACH tbl IN ARRAY required_tables
    LOOP
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_name = tbl AND table_schema = 'public'
        ) THEN
            missing_tables := array_append(missing_tables, tbl);
        END IF;
    END LOOP;
    
    IF array_length(missing_tables, 1) > 0 THEN
        RAISE WARNING 'Missing tables: %', array_to_string(missing_tables, ', ');
        RAISE NOTICE 'You may need to run 001_complete_schema.sql first';
    ELSE
        RAISE NOTICE 'All required tables exist!';
    END IF;
    
    RAISE NOTICE 'Migration 007_fix_missing_tables completed';
END $$;
