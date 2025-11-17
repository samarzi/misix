-- Fix users table - add missing columns
-- Apply this in Supabase SQL Editor

-- Add missing columns to users table
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS first_name TEXT,
ADD COLUMN IF NOT EXISTS last_name TEXT,
ADD COLUMN IF NOT EXISTS full_name TEXT,
ADD COLUMN IF NOT EXISTS email TEXT,
ADD COLUMN IF NOT EXISTS password_hash TEXT,
ADD COLUMN IF NOT EXISTS avatar_url TEXT,
ADD COLUMN IF NOT EXISTS bio TEXT,
ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE;

-- Update existing users with default values
UPDATE users 
SET 
    first_name = COALESCE(first_name, username, 'User'),
    last_name = COALESCE(last_name, ''),
    full_name = COALESCE(full_name, username, CONCAT('User ', id)),
    email = COALESCE(email, CONCAT('user_', id, '@misix.local')),
    password_hash = COALESCE(password_hash, '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIxF6k0O3i')
WHERE first_name IS NULL OR email IS NULL OR password_hash IS NULL;

-- Make required columns NOT NULL
ALTER TABLE users 
ALTER COLUMN first_name SET NOT NULL,
ALTER COLUMN full_name SET NOT NULL,
ALTER COLUMN email SET NOT NULL,
ALTER COLUMN password_hash SET NOT NULL;

-- Add unique constraint on email
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_unique ON users(email);

-- Verify
SELECT 
    column_name, 
    data_type, 
    is_nullable
FROM information_schema.columns
WHERE table_name = 'users'
ORDER BY ordinal_position;
