-- Add missing columns to existing tables
-- Safe to run multiple times (uses IF NOT EXISTS where possible)

-- ============================================================================
-- Add missing columns to note_folders
-- ============================================================================

-- Check if parent_id column exists, if not add it
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'note_folders' AND column_name = 'parent_id'
    ) THEN
        ALTER TABLE note_folders ADD COLUMN parent_id uuid;
        
        -- Add foreign key constraint
        ALTER TABLE note_folders 
        ADD CONSTRAINT note_folders_parent_fk 
        FOREIGN KEY (parent_id) REFERENCES note_folders (id) ON DELETE CASCADE;
        
        -- Add index
        CREATE INDEX idx_note_folders_parent ON note_folders (parent_id);
    END IF;
END $$;

-- Check if color column exists
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'note_folders' AND column_name = 'color'
    ) THEN
        ALTER TABLE note_folders ADD COLUMN color text;
    END IF;
END $$;

-- ============================================================================
-- Add missing columns to users
-- ============================================================================

DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'telegram_id'
    ) THEN
        ALTER TABLE users ADD COLUMN telegram_id bigint UNIQUE;
        CREATE INDEX idx_users_telegram_id ON users (telegram_id);
    END IF;
END $$;

DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'username'
    ) THEN
        ALTER TABLE users ADD COLUMN username text;
    END IF;
END $$;

-- ============================================================================
-- Add missing columns to notes
-- ============================================================================

DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'notes' AND column_name = 'folder_id'
    ) THEN
        ALTER TABLE notes ADD COLUMN folder_id uuid;
        
        -- Add foreign key constraint if note_folders table exists
        IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'note_folders') THEN
            ALTER TABLE notes 
            ADD CONSTRAINT notes_folder_fk 
            FOREIGN KEY (folder_id) REFERENCES note_folders (id) ON DELETE SET NULL;
            
            CREATE INDEX idx_notes_folder ON notes (folder_id);
        END IF;
    END IF;
END $$;

DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'notes' AND column_name = 'telegram_id'
    ) THEN
        ALTER TABLE notes ADD COLUMN telegram_id bigint;
    END IF;
END $$;

DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'notes' AND column_name = 'is_favorite'
    ) THEN
        ALTER TABLE notes ADD COLUMN is_favorite boolean DEFAULT false;
        CREATE INDEX idx_notes_favorite ON notes (user_id, is_favorite);
    END IF;
END $$;

DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'notes' AND column_name = 'is_archived'
    ) THEN
        ALTER TABLE notes ADD COLUMN is_archived boolean DEFAULT false;
        CREATE INDEX idx_notes_archived ON notes (user_id, is_archived);
    END IF;
END $$;

DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'notes' AND column_name = 'content_format'
    ) THEN
        ALTER TABLE notes ADD COLUMN content_format text DEFAULT 'markdown';
    END IF;
END $$;

-- ============================================================================
-- Add missing columns to tasks
-- ============================================================================

DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tasks' AND column_name = 'telegram_id'
    ) THEN
        ALTER TABLE tasks ADD COLUMN telegram_id bigint;
    END IF;
END $$;

DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tasks' AND column_name = 'project_id'
    ) THEN
        ALTER TABLE tasks ADD COLUMN project_id uuid;
        
        -- Add foreign key constraint if projects table exists
        IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'projects') THEN
            ALTER TABLE tasks 
            ADD CONSTRAINT tasks_project_fk 
            FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE SET NULL;
            
            CREATE INDEX idx_tasks_project ON tasks (project_id);
        END IF;
    END IF;
END $$;

DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tasks' AND column_name = 'parent_task_id'
    ) THEN
        ALTER TABLE tasks ADD COLUMN parent_task_id uuid;
        
        ALTER TABLE tasks 
        ADD CONSTRAINT tasks_parent_fk 
        FOREIGN KEY (parent_task_id) REFERENCES tasks (id) ON DELETE CASCADE;
        
        CREATE INDEX idx_tasks_parent ON tasks (parent_task_id);
    END IF;
END $$;

DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tasks' AND column_name = 'assigned_to'
    ) THEN
        ALTER TABLE tasks ADD COLUMN assigned_to uuid;
        
        ALTER TABLE tasks 
        ADD CONSTRAINT tasks_assigned_fk 
        FOREIGN KEY (assigned_to) REFERENCES users (id) ON DELETE SET NULL;
    END IF;
END $$;

DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tasks' AND column_name = 'priority'
    ) THEN
        ALTER TABLE tasks ADD COLUMN priority text DEFAULT 'medium' 
        CHECK (priority IN ('low', 'medium', 'high', 'critical'));
    END IF;
END $$;

DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tasks' AND column_name = 'status'
    ) THEN
        ALTER TABLE tasks ADD COLUMN status text DEFAULT 'new' 
        CHECK (status IN ('new', 'in_progress', 'waiting', 'completed', 'cancelled'));
    END IF;
END $$;

DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tasks' AND column_name = 'deadline'
    ) THEN
        ALTER TABLE tasks ADD COLUMN deadline timestamptz;
        CREATE INDEX idx_tasks_deadline ON tasks (user_id, deadline);
    END IF;
END $$;

DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tasks' AND column_name = 'estimated_hours'
    ) THEN
        ALTER TABLE tasks ADD COLUMN estimated_hours decimal(4,1);
    END IF;
END $$;

DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tasks' AND column_name = 'actual_hours'
    ) THEN
        ALTER TABLE tasks ADD COLUMN actual_hours decimal(4,1);
    END IF;
END $$;

DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tasks' AND column_name = 'is_recurring'
    ) THEN
        ALTER TABLE tasks ADD COLUMN is_recurring boolean DEFAULT false;
    END IF;
END $$;

DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tasks' AND column_name = 'recurrence_rule'
    ) THEN
        ALTER TABLE tasks ADD COLUMN recurrence_rule text;
    END IF;
END $$;

-- ============================================================================
-- Add missing columns to assistant_sessions
-- ============================================================================

DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'assistant_sessions' AND column_name = 'telegram_id'
    ) THEN
        ALTER TABLE assistant_sessions ADD COLUMN telegram_id bigint;
    END IF;
END $$;

-- ============================================================================
-- Add missing columns to assistant_messages
-- ============================================================================

DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'assistant_messages' AND column_name = 'telegram_id'
    ) THEN
        ALTER TABLE assistant_messages ADD COLUMN telegram_id bigint;
    END IF;
END $$;

-- ============================================================================
-- Verify all columns were added
-- ============================================================================

-- You can run this query to check which columns exist:
-- SELECT table_name, column_name, data_type 
-- FROM information_schema.columns 
-- WHERE table_schema = 'public' 
-- ORDER BY table_name, ordinal_position;

