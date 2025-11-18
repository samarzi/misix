-- Migration: Remove email authentication from users table
-- Description: Remove email, password_hash, and email_verified columns
--              Make telegram_id NOT NULL as it's the only authentication method
-- Date: 2025-11-18

-- Start transaction
BEGIN;

-- Drop index on email if it exists
DROP INDEX IF EXISTS idx_users_email;

-- Drop email_verified column if it exists
ALTER TABLE users DROP COLUMN IF EXISTS email_verified;

-- Drop password_hash column if it exists
ALTER TABLE users DROP COLUMN IF EXISTS password_hash;

-- Drop email column if it exists (must be last due to unique constraint)
ALTER TABLE users DROP COLUMN IF EXISTS email;

-- Make telegram_id NOT NULL (required for all users)
-- First check if there are any NULL values
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM users WHERE telegram_id IS NULL) THEN
        RAISE EXCEPTION 'Cannot make telegram_id NOT NULL: found users with NULL telegram_id. Please fix data first.';
    END IF;
END $$;

-- Set telegram_id to NOT NULL
ALTER TABLE users ALTER COLUMN telegram_id SET NOT NULL;

-- Ensure telegram_id index exists and is unique
DROP INDEX IF EXISTS idx_users_telegram_id;
CREATE UNIQUE INDEX idx_users_telegram_id ON users (telegram_id);

-- Commit transaction
COMMIT;

-- Verify the changes
DO $$
DECLARE
    email_exists boolean;
    password_exists boolean;
    email_verified_exists boolean;
    telegram_nullable boolean;
BEGIN
    -- Check if email column still exists
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'email'
    ) INTO email_exists;
    
    -- Check if password_hash column still exists
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'password_hash'
    ) INTO password_exists;
    
    -- Check if email_verified column still exists
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'email_verified'
    ) INTO email_verified_exists;
    
    -- Check if telegram_id is nullable
    SELECT is_nullable = 'YES' FROM information_schema.columns 
    WHERE table_name = 'users' AND column_name = 'telegram_id'
    INTO telegram_nullable;
    
    -- Report results
    IF email_exists THEN
        RAISE WARNING 'email column still exists!';
    ELSE
        RAISE NOTICE '✅ email column removed successfully';
    END IF;
    
    IF password_exists THEN
        RAISE WARNING 'password_hash column still exists!';
    ELSE
        RAISE NOTICE '✅ password_hash column removed successfully';
    END IF;
    
    IF email_verified_exists THEN
        RAISE WARNING 'email_verified column still exists!';
    ELSE
        RAISE NOTICE '✅ email_verified column removed successfully';
    END IF;
    
    IF telegram_nullable THEN
        RAISE WARNING 'telegram_id is still nullable!';
    ELSE
        RAISE NOTICE '✅ telegram_id is now NOT NULL';
    END IF;
    
    RAISE NOTICE '✅ Migration 009_remove_email_auth completed successfully';
END $$;
