-- ============================================================================
-- ADD MISSING COLUMNS TO EXISTING TABLES
-- ============================================================================
-- Этот файл добавляет недостающие колонки к существующим таблицам
-- Безопасно применять несколько раз
-- ============================================================================

-- Add missing columns to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS first_name TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_name TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS email TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS bio TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE;

-- Update NULL values with defaults
UPDATE users 
SET 
    first_name = COALESCE(first_name, username, 'User'),
    last_name = COALESCE(last_name, ''),
    full_name = COALESCE(full_name, username, CONCAT('User_', id)),
    email = COALESCE(email, CONCAT('user_', REPLACE(id::TEXT, '-', ''), '@misix.local')),
    password_hash = COALESCE(password_hash, '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIxF6k0O3i')
WHERE first_name IS NULL OR email IS NULL OR password_hash IS NULL OR full_name IS NULL;

-- Add missing column to tasks table
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS last_reminder_sent_at TIMESTAMPTZ;

-- Create indexes if they don't exist
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_tasks_deadline_active ON tasks(deadline) 
    WHERE status != 'completed' AND deadline IS NOT NULL;

SELECT 'Missing columns added successfully!' AS status;
