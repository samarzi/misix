-- MISIX Complete Database Schema
-- This migration creates all tables and relationships
-- Safe to run multiple times (uses IF NOT EXISTS)

-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- Create timestamp trigger function
create or replace function trigger_set_timestamp()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

-- ============================================================================
-- USERS TABLE
-- ============================================================================

create table if not exists users (
    id uuid primary key default uuid_generate_v4(),
    email text unique not null,
    password_hash text not null,
    full_name text not null,
    avatar_url text,
    bio text,
    telegram_id bigint unique,
    username text,
    language_code text,
    email_verified boolean default false,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

drop trigger if exists set_users_updated_at on users;
create trigger set_users_updated_at
    before update on users
    for each row
    execute procedure trigger_set_timestamp();

create index if not exists idx_users_email on users (email);
create index if not exists idx_users_telegram_id on users (telegram_id);

-- ============================================================================
-- NOTE FOLDERS TABLE
-- ============================================================================

create table if not exists note_folders (
    id uuid primary key default uuid_generate_v4(),
    user_id uuid not null,
    name text not null,
    parent_id uuid,
    color text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint note_folders_user_fk foreign key (user_id)
        references users (id) on delete cascade,
    constraint note_folders_parent_fk foreign key (parent_id)
        references note_folders (id) on delete cascade
);

drop trigger if exists set_note_folders_updated_at on note_folders;
create trigger set_note_folders_updated_at
    before update on note_folders
    for each row
    execute procedure trigger_set_timestamp();

create index if not exists idx_note_folders_user on note_folders (user_id);
create index if not exists idx_note_folders_parent on note_folders (parent_id);

-- ============================================================================
-- TAGS TABLE
-- ============================================================================

create table if not exists tags (
    id uuid primary key default uuid_generate_v4(),
    user_id uuid not null,
    name text not null,
    color text,
    created_at timestamptz not null default now(),
    constraint tags_user_fk foreign key (user_id)
        references users (id) on delete cascade,
    constraint tags_user_name_unique unique (user_id, name)
);

create index if not exists idx_tags_user on tags (user_id);

-- ============================================================================
-- PROJECTS TABLE
-- ============================================================================

create table if not exists projects (
    id uuid primary key default uuid_generate_v4(),
    user_id uuid not null,
    name text not null,
    description text,
    color text,
    deadline timestamptz,
    status text default 'active',
    progress_percent integer default 0 check (progress_percent >= 0 and progress_percent <= 100),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint projects_user_fk foreign key (user_id)
        references users (id) on delete cascade
);

drop trigger if exists set_projects_updated_at on projects;
create trigger set_projects_updated_at
    before update on projects
    for each row
    execute procedure trigger_set_timestamp();

create index if not exists idx_projects_user on projects (user_id);
create index if not exists idx_projects_status on projects (user_id, status);

-- ============================================================================
-- NOTES TABLE
-- ============================================================================

create table if not exists notes (
    id uuid primary key default uuid_generate_v4(),
    user_id uuid not null,
    folder_id uuid,
    telegram_id bigint,
    title text,
    content text not null,
    content_format text default 'markdown',
    is_favorite boolean default false,
    is_archived boolean default false,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint notes_user_fk foreign key (user_id)
        references users (id) on delete cascade,
    constraint notes_folder_fk foreign key (folder_id)
        references note_folders (id) on delete set null
);

drop trigger if exists set_notes_updated_at on notes;
create trigger set_notes_updated_at
    before update on notes
    for each row
    execute procedure trigger_set_timestamp();

create index if not exists idx_notes_user on notes (user_id);
create index if not exists idx_notes_folder on notes (folder_id);
create index if not exists idx_notes_favorite on notes (user_id, is_favorite);
create index if not exists idx_notes_archived on notes (user_id, is_archived);

-- ============================================================================
-- NOTE TAGS (Many-to-Many)
-- ============================================================================

create table if not exists note_tags (
    note_id uuid not null,
    tag_id uuid not null,
    created_at timestamptz not null default now(),
    primary key (note_id, tag_id),
    constraint note_tags_note_fk foreign key (note_id)
        references notes (id) on delete cascade,
    constraint note_tags_tag_fk foreign key (tag_id)
        references tags (id) on delete cascade
);

-- ============================================================================
-- TASKS TABLE
-- ============================================================================

create table if not exists tasks (
    id uuid primary key default uuid_generate_v4(),
    user_id uuid not null,
    project_id uuid,
    parent_task_id uuid,
    telegram_id bigint,
    title text not null,
    description text,
    priority text default 'medium' check (priority in ('low', 'medium', 'high', 'critical')),
    status text default 'new' check (status in ('new', 'in_progress', 'waiting', 'completed', 'cancelled')),
    deadline timestamptz,
    estimated_hours decimal(4,1),
    actual_hours decimal(4,1),
    is_recurring boolean default false,
    recurrence_rule text,
    assigned_to uuid,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint tasks_user_fk foreign key (user_id)
        references users (id) on delete cascade,
    constraint tasks_project_fk foreign key (project_id)
        references projects (id) on delete set null,
    constraint tasks_parent_fk foreign key (parent_task_id)
        references tasks (id) on delete cascade,
    constraint tasks_assigned_fk foreign key (assigned_to)
        references users (id) on delete set null
);

drop trigger if exists set_tasks_updated_at on tasks;
create trigger set_tasks_updated_at
    before update on tasks
    for each row
    execute procedure trigger_set_timestamp();

create index if not exists idx_tasks_user on tasks (user_id);
create index if not exists idx_tasks_project on tasks (project_id);
create index if not exists idx_tasks_status on tasks (user_id, status);
create index if not exists idx_tasks_priority on tasks (user_id, priority);
create index if not exists idx_tasks_deadline on tasks (user_id, deadline);
create index if not exists idx_tasks_parent on tasks (parent_task_id);

-- ============================================================================
-- TASK TAGS (Many-to-Many)
-- ============================================================================

create table if not exists task_tags (
    task_id uuid not null,
    tag_id uuid not null,
    created_at timestamptz not null default now(),
    primary key (task_id, tag_id),
    constraint task_tags_task_fk foreign key (task_id)
        references tasks (id) on delete cascade,
    constraint task_tags_tag_fk foreign key (tag_id)
        references tags (id) on delete cascade
);

-- ============================================================================
-- TASK SUBITEMS
-- ============================================================================

create table if not exists task_subitems (
    id uuid primary key default uuid_generate_v4(),
    task_id uuid not null,
    content text not null,
    is_completed boolean default false,
    sort_order integer default 0,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint task_subitems_task_fk foreign key (task_id)
        references tasks (id) on delete cascade
);

drop trigger if exists set_task_subitems_updated_at on task_subitems;
create trigger set_task_subitems_updated_at
    before update on task_subitems
    for each row
    execute procedure trigger_set_timestamp();

create index if not exists idx_task_subitems_task on task_subitems (task_id);

-- ============================================================================
-- ASSISTANT SESSIONS
-- ============================================================================

create table if not exists assistant_sessions (
    id uuid primary key default uuid_generate_v4(),
    user_id uuid not null,
    telegram_id bigint,
    title text,
    model text default 'gpt-4',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint assistant_sessions_user_fk foreign key (user_id)
        references users (id) on delete cascade
);

drop trigger if exists set_assistant_sessions_updated_at on assistant_sessions;
create trigger set_assistant_sessions_updated_at
    before update on assistant_sessions
    for each row
    execute procedure trigger_set_timestamp();

create index if not exists idx_assistant_sessions_user on assistant_sessions (user_id);

-- ============================================================================
-- ASSISTANT MESSAGES
-- ============================================================================

create table if not exists assistant_messages (
    id uuid primary key default uuid_generate_v4(),
    session_id uuid,
    user_id uuid not null,
    telegram_id bigint,
    role text not null check (role in ('user', 'assistant', 'system')),
    content text not null,
    tokens_used integer,
    model text,
    created_at timestamptz not null default now(),
    constraint assistant_messages_session_fk foreign key (session_id)
        references assistant_sessions (id) on delete set null,
    constraint assistant_messages_user_fk foreign key (user_id)
        references users (id) on delete cascade
);

create index if not exists idx_assistant_messages_session on assistant_messages (session_id);
create index if not exists idx_assistant_messages_user on assistant_messages (user_id);

-- ============================================================================
-- ATTACHMENTS
-- ============================================================================

create table if not exists attachments (
    id uuid primary key default uuid_generate_v4(),
    user_id uuid not null,
    entity_type text not null check (entity_type in ('note', 'task')),
    entity_id uuid not null,
    filename text not null,
    file_path text not null,
    file_size integer not null,
    mime_type text not null,
    created_at timestamptz not null default now(),
    constraint attachments_user_fk foreign key (user_id)
        references users (id) on delete cascade
);

create index if not exists idx_attachments_entity on attachments (entity_type, entity_id);
create index if not exists idx_attachments_user on attachments (user_id);

-- ============================================================================
-- SLEEP SESSIONS
-- ============================================================================

create table if not exists sleep_sessions (
    id uuid primary key default uuid_generate_v4(),
    user_id uuid not null,
    status text not null check (status in ('pending', 'sleeping', 'paused', 'finished', 'auto_stopped')),
    initiated_at timestamptz not null,
    sleep_started_at timestamptz,
    sleep_ended_at timestamptz,
    auto_stop_at timestamptz,
    total_sleep_seconds integer default 0,
    total_pause_seconds integer default 0,
    last_state_change timestamptz not null,
    paused_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint sleep_sessions_user_fk foreign key (user_id)
        references users (id) on delete cascade
);

drop trigger if exists set_sleep_sessions_updated_at on sleep_sessions;
create trigger set_sleep_sessions_updated_at
    before update on sleep_sessions
    for each row
    execute procedure trigger_set_timestamp();

create index if not exists idx_sleep_sessions_user on sleep_sessions (user_id);
create index if not exists idx_sleep_sessions_status on sleep_sessions (user_id, status);

-- ============================================================================
-- FINANCES (if needed - add your finance tables here)
-- ============================================================================

-- Add any additional tables you need below

