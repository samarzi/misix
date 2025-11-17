-- Migration: Add database indexes for performance optimization
-- Description: Add indexes on frequently queried fields

-- Tasks table indexes
CREATE INDEX IF NOT EXISTS idx_tasks_user_status 
ON tasks(user_id, status);

CREATE INDEX IF NOT EXISTS idx_tasks_user_priority 
ON tasks(user_id, priority);

CREATE INDEX IF NOT EXISTS idx_tasks_user_created 
ON tasks(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_tasks_project 
ON tasks(project_id) 
WHERE project_id IS NOT NULL;

-- Finance entries indexes
CREATE INDEX IF NOT EXISTS idx_finance_user_type 
ON finance_entries(user_id, type);

CREATE INDEX IF NOT EXISTS idx_finance_user_date 
ON finance_entries(user_id, date DESC);

CREATE INDEX IF NOT EXISTS idx_finance_user_category 
ON finance_entries(user_id, category);

CREATE INDEX IF NOT EXISTS idx_finance_date_range 
ON finance_entries(date) 
WHERE date IS NOT NULL;

-- Notes indexes
CREATE INDEX IF NOT EXISTS idx_notes_user_created 
ON notes(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_notes_user_updated 
ON notes(user_id, updated_at DESC);

-- Personal entries indexes
CREATE INDEX IF NOT EXISTS idx_personal_user_created 
ON personal_entries(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_personal_user_type 
ON personal_entries(user_id, entry_type);

-- Mood entries indexes (already created in 004_add_mood_entries.sql, but ensuring)
CREATE INDEX IF NOT EXISTS idx_mood_user_created 
ON mood_entries(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_mood_user_mood 
ON mood_entries(user_id, mood);

-- Sleep tracking indexes
CREATE INDEX IF NOT EXISTS idx_sleep_user_date 
ON sleep_tracking(user_id, sleep_date DESC);

CREATE INDEX IF NOT EXISTS idx_sleep_user_start 
ON sleep_tracking(user_id, sleep_start DESC);

-- Users indexes
CREATE INDEX IF NOT EXISTS idx_users_telegram 
ON users(telegram_id) 
WHERE telegram_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_users_email 
ON users(email) 
WHERE email IS NOT NULL;

-- Verify indexes created
DO $$
DECLARE
    index_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO index_count
    FROM pg_indexes
    WHERE schemaname = 'public'
    AND indexname LIKE 'idx_%';
    
    RAISE NOTICE 'Total indexes created: %', index_count;
    RAISE NOTICE 'Migration 006_add_indexes completed successfully';
END $$;
