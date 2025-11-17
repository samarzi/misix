-- WARNING: This will DELETE ALL DATA and recreate the schema from scratch
-- Only use this if you're okay with losing all existing data
-- 
-- To use this safely:
-- 1. First backup your data if needed
-- 2. Run this script
-- 3. Your database will be completely reset with the correct schema

-- ============================================================================
-- STEP 1: Drop all existing tables (CASCADE removes dependencies)
-- ============================================================================

DROP TABLE IF EXISTS sleep_sessions CASCADE;
DROP TABLE IF EXISTS attachments CASCADE;
DROP TABLE IF EXISTS assistant_messages CASCADE;
DROP TABLE IF EXISTS assistant_sessions CASCADE;
DROP TABLE IF EXISTS task_subitems CASCADE;
DROP TABLE IF EXISTS task_tags CASCADE;
DROP TABLE IF EXISTS note_tags CASCADE;
DROP TABLE IF EXISTS tasks CASCADE;
DROP TABLE IF EXISTS notes CASCADE;
DROP TABLE IF EXISTS projects CASCADE;
DROP TABLE IF EXISTS tags CASCADE;
DROP TABLE IF EXISTS note_folders CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Drop the trigger function if it exists
DROP FUNCTION IF EXISTS trigger_set_timestamp() CASCADE;

-- ============================================================================
-- STEP 2: Create everything from scratch
-- ============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create timestamp trigger function
CREATE OR REPLACE FUNCTION trigger_set_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- USERS TABLE
-- ============================================================================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    avatar_url TEXT,
    bio TEXT,
    telegram_id BIGINT UNIQUE,
    username TEXT,
    language_code TEXT,
    email_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TRIGGER set_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE PROCEDURE trigger_set_timestamp();

CREATE INDEX idx_users_email ON users (email);
CREATE INDEX idx_users_telegram_id ON users (telegram_id);

-- ============================================================================
-- NOTE FOLDERS TABLE
-- ============================================================================

CREATE TABLE note_folders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    name TEXT NOT NULL,
    parent_id UUID,
    color TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT note_folders_user_fk FOREIGN KEY (user_id)
        REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT note_folders_parent_fk FOREIGN KEY (parent_id)
        REFERENCES note_folders (id) ON DELETE CASCADE
);

CREATE TRIGGER set_note_folders_updated_at
    BEFORE UPDATE ON note_folders
    FOR EACH ROW
    EXECUTE PROCEDURE trigger_set_timestamp();

CREATE INDEX idx_note_folders_user ON note_folders (user_id);
CREATE INDEX idx_note_folders_parent ON note_folders (parent_id);

-- ============================================================================
-- TAGS TABLE
-- ============================================================================

CREATE TABLE tags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    name TEXT NOT NULL,
    color TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT tags_user_fk FOREIGN KEY (user_id)
        REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT tags_user_name_unique UNIQUE (user_id, name)
);

CREATE INDEX idx_tags_user ON tags (user_id);

-- ============================================================================
-- PROJECTS TABLE
-- ============================================================================

CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    color TEXT,
    deadline TIMESTAMPTZ,
    status TEXT DEFAULT 'active',
    progress_percent INTEGER DEFAULT 0 CHECK (progress_percent >= 0 AND progress_percent <= 100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT projects_user_fk FOREIGN KEY (user_id)
        REFERENCES users (id) ON DELETE CASCADE
);

CREATE TRIGGER set_projects_updated_at
    BEFORE UPDATE ON projects
    FOR EACH ROW
    EXECUTE PROCEDURE trigger_set_timestamp();

CREATE INDEX idx_projects_user ON projects (user_id);
CREATE INDEX idx_projects_status ON projects (user_id, status);

-- ============================================================================
-- NOTES TABLE
-- ============================================================================

CREATE TABLE notes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    folder_id UUID,
    telegram_id BIGINT,
    title TEXT,
    content TEXT NOT NULL,
    content_format TEXT DEFAULT 'markdown',
    is_favorite BOOLEAN DEFAULT FALSE,
    is_archived BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT notes_user_fk FOREIGN KEY (user_id)
        REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT notes_folder_fk FOREIGN KEY (folder_id)
        REFERENCES note_folders (id) ON DELETE SET NULL
);

CREATE TRIGGER set_notes_updated_at
    BEFORE UPDATE ON notes
    FOR EACH ROW
    EXECUTE PROCEDURE trigger_set_timestamp();

CREATE INDEX idx_notes_user ON notes (user_id);
CREATE INDEX idx_notes_folder ON notes (folder_id);
CREATE INDEX idx_notes_favorite ON notes (user_id, is_favorite);
CREATE INDEX idx_notes_archived ON notes (user_id, is_archived);

-- ============================================================================
-- NOTE TAGS (Many-to-Many)
-- ============================================================================

CREATE TABLE note_tags (
    note_id UUID NOT NULL,
    tag_id UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (note_id, tag_id),
    CONSTRAINT note_tags_note_fk FOREIGN KEY (note_id)
        REFERENCES notes (id) ON DELETE CASCADE,
    CONSTRAINT note_tags_tag_fk FOREIGN KEY (tag_id)
        REFERENCES tags (id) ON DELETE CASCADE
);

-- ============================================================================
-- TASKS TABLE
-- ============================================================================

CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    project_id UUID,
    parent_task_id UUID,
    telegram_id BIGINT,
    title TEXT NOT NULL,
    description TEXT,
    priority TEXT DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    status TEXT DEFAULT 'new' CHECK (status IN ('new', 'in_progress', 'waiting', 'completed', 'cancelled')),
    deadline TIMESTAMPTZ,
    estimated_hours DECIMAL(4,1),
    actual_hours DECIMAL(4,1),
    is_recurring BOOLEAN DEFAULT FALSE,
    recurrence_rule TEXT,
    assigned_to UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT tasks_user_fk FOREIGN KEY (user_id)
        REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT tasks_project_fk FOREIGN KEY (project_id)
        REFERENCES projects (id) ON DELETE SET NULL,
    CONSTRAINT tasks_parent_fk FOREIGN KEY (parent_task_id)
        REFERENCES tasks (id) ON DELETE CASCADE,
    CONSTRAINT tasks_assigned_fk FOREIGN KEY (assigned_to)
        REFERENCES users (id) ON DELETE SET NULL
);

CREATE TRIGGER set_tasks_updated_at
    BEFORE UPDATE ON tasks
    FOR EACH ROW
    EXECUTE PROCEDURE trigger_set_timestamp();

CREATE INDEX idx_tasks_user ON tasks (user_id);
CREATE INDEX idx_tasks_project ON tasks (project_id);
CREATE INDEX idx_tasks_status ON tasks (user_id, status);
CREATE INDEX idx_tasks_priority ON tasks (user_id, priority);
CREATE INDEX idx_tasks_deadline ON tasks (user_id, deadline);
CREATE INDEX idx_tasks_parent ON tasks (parent_task_id);

-- ============================================================================
-- TASK TAGS (Many-to-Many)
-- ============================================================================

CREATE TABLE task_tags (
    task_id UUID NOT NULL,
    tag_id UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (task_id, tag_id),
    CONSTRAINT task_tags_task_fk FOREIGN KEY (task_id)
        REFERENCES tasks (id) ON DELETE CASCADE,
    CONSTRAINT task_tags_tag_fk FOREIGN KEY (tag_id)
        REFERENCES tags (id) ON DELETE CASCADE
);

-- ============================================================================
-- TASK SUBITEMS
-- ============================================================================

CREATE TABLE task_subitems (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL,
    content TEXT NOT NULL,
    is_completed BOOLEAN DEFAULT FALSE,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT task_subitems_task_fk FOREIGN KEY (task_id)
        REFERENCES tasks (id) ON DELETE CASCADE
);

CREATE TRIGGER set_task_subitems_updated_at
    BEFORE UPDATE ON task_subitems
    FOR EACH ROW
    EXECUTE PROCEDURE trigger_set_timestamp();

CREATE INDEX idx_task_subitems_task ON task_subitems (task_id);

-- ============================================================================
-- ASSISTANT SESSIONS
-- ============================================================================

CREATE TABLE assistant_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    telegram_id BIGINT,
    title TEXT,
    model TEXT DEFAULT 'gpt-4',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT assistant_sessions_user_fk FOREIGN KEY (user_id)
        REFERENCES users (id) ON DELETE CASCADE
);

CREATE TRIGGER set_assistant_sessions_updated_at
    BEFORE UPDATE ON assistant_sessions
    FOR EACH ROW
    EXECUTE PROCEDURE trigger_set_timestamp();

CREATE INDEX idx_assistant_sessions_user ON assistant_sessions (user_id);

-- ============================================================================
-- ASSISTANT MESSAGES
-- ============================================================================

CREATE TABLE assistant_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID,
    user_id UUID NOT NULL,
    telegram_id BIGINT,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    tokens_used INTEGER,
    model TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT assistant_messages_session_fk FOREIGN KEY (session_id)
        REFERENCES assistant_sessions (id) ON DELETE SET NULL,
    CONSTRAINT assistant_messages_user_fk FOREIGN KEY (user_id)
        REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX idx_assistant_messages_session ON assistant_messages (session_id);
CREATE INDEX idx_assistant_messages_user ON assistant_messages (user_id);

-- ============================================================================
-- ATTACHMENTS
-- ============================================================================

CREATE TABLE attachments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    entity_type TEXT NOT NULL CHECK (entity_type IN ('note', 'task')),
    entity_id UUID NOT NULL,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    mime_type TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT attachments_user_fk FOREIGN KEY (user_id)
        REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX idx_attachments_entity ON attachments (entity_type, entity_id);
CREATE INDEX idx_attachments_user ON attachments (user_id);

-- ============================================================================
-- SLEEP SESSIONS
-- ============================================================================

CREATE TABLE sleep_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'sleeping', 'paused', 'finished', 'auto_stopped')),
    initiated_at TIMESTAMPTZ NOT NULL,
    sleep_started_at TIMESTAMPTZ,
    sleep_ended_at TIMESTAMPTZ,
    auto_stop_at TIMESTAMPTZ,
    total_sleep_seconds INTEGER DEFAULT 0,
    total_pause_seconds INTEGER DEFAULT 0,
    last_state_change TIMESTAMPTZ NOT NULL,
    paused_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT sleep_sessions_user_fk FOREIGN KEY (user_id)
        REFERENCES users (id) ON DELETE CASCADE
);

CREATE TRIGGER set_sleep_sessions_updated_at
    BEFORE UPDATE ON sleep_sessions
    FOR EACH ROW
    EXECUTE PROCEDURE trigger_set_timestamp();

CREATE INDEX idx_sleep_sessions_user ON sleep_sessions (user_id);
CREATE INDEX idx_sleep_sessions_status ON sleep_sessions (user_id, status);

-- ============================================================================
-- DONE!
-- ============================================================================

SELECT 'Database schema created successfully!' AS status;
