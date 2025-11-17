-- Migration: Add reminders support
-- Description: Add fields and tables for task reminders and user settings

-- Add last_reminder_sent_at to tasks table
ALTER TABLE tasks 
ADD COLUMN IF NOT EXISTS last_reminder_sent_at TIMESTAMPTZ;

-- Create index on deadline for fast reminder queries
CREATE INDEX IF NOT EXISTS idx_tasks_deadline_active 
ON tasks(deadline) 
WHERE status != 'completed' AND deadline IS NOT NULL;

-- Create user_settings table for reminder preferences
CREATE TABLE IF NOT EXISTS user_settings (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    reminders_enabled BOOLEAN DEFAULT true,
    daily_summary_time TIME DEFAULT '09:00',
    reminder_minutes_before INTEGER DEFAULT 60,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index on user_settings for active reminders
CREATE INDEX IF NOT EXISTS idx_user_settings_reminders_enabled 
ON user_settings(reminders_enabled) 
WHERE reminders_enabled = true;

-- Add trigger to update updated_at
CREATE OR REPLACE FUNCTION update_user_settings_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_user_settings_updated_at
    BEFORE UPDATE ON user_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_user_settings_updated_at();

-- Verify migration
DO $$
BEGIN
    -- Check tasks column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tasks' AND column_name = 'last_reminder_sent_at'
    ) THEN
        RAISE EXCEPTION 'Migration failed: last_reminder_sent_at column not created';
    END IF;
    
    -- Check user_settings table
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'user_settings'
    ) THEN
        RAISE EXCEPTION 'Migration failed: user_settings table not created';
    END IF;
    
    RAISE NOTICE 'Migration 005_add_reminders completed successfully';
END $$;
