-- Add mood_entries table for mood tracking
-- Migration: 004_add_mood_entries
-- Date: 2025-11-17

-- ============================================================================
-- MOOD ENTRIES TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS mood_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    mood TEXT NOT NULL,
    intensity INTEGER NOT NULL CHECK (intensity >= 1 AND intensity <= 10),
    note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT mood_entries_user_fk FOREIGN KEY (user_id)
        REFERENCES users (id) ON DELETE CASCADE
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_mood_entries_user ON mood_entries(user_id);
CREATE INDEX IF NOT EXISTS idx_mood_entries_created ON mood_entries(created_at);
CREATE INDEX IF NOT EXISTS idx_mood_entries_user_created ON mood_entries(user_id, created_at DESC);

-- Create trigger for updated_at
DROP TRIGGER IF EXISTS set_mood_entries_updated_at ON mood_entries;
CREATE TRIGGER set_mood_entries_updated_at
    BEFORE UPDATE ON mood_entries
    FOR EACH ROW
    EXECUTE PROCEDURE trigger_set_timestamp();

-- Add comment
COMMENT ON TABLE mood_entries IS 'User mood tracking entries';
COMMENT ON COLUMN mood_entries.mood IS 'Mood type: happy, sad, anxious, calm, excited, tired, stressed, angry, neutral';
COMMENT ON COLUMN mood_entries.intensity IS 'Mood intensity from 1 (low) to 10 (high)';
