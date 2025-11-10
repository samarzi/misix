-- Fix assistant_messages schema: add missing user_id column
-- Run this in Supabase SQL Editor

-- Step 1: Add the user_id column
ALTER TABLE public.assistant_messages ADD COLUMN IF NOT EXISTS user_id UUID;

-- Step 2: Populate user_id for existing records using telegram_id
UPDATE public.assistant_messages m
SET user_id = u.id
FROM public.users u
WHERE m.user_id IS NULL
  AND m.telegram_id = u.telegram_id;

-- Step 3: (Optional) Make user_id NOT NULL if needed, but only after populating all rows
-- ALTER TABLE public.assistant_messages ALTER COLUMN user_id SET NOT NULL;

-- Step 4: Create index if not exists (from schema.sql)
CREATE INDEX IF NOT EXISTS idx_assistant_messages_user ON assistant_messages (user_id);
