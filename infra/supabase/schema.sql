-- MISIX Supabase schema for full web application with authentication

create extension if not exists "uuid-ossp";

create or replace function trigger_set_timestamp()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

-- Users table with full authentication support
create table if not exists users (
    id uuid primary key default uuid_generate_v4(),
    email text unique not null,
    password_hash text not null,
    full_name text not null,
    avatar_url text,
    bio text,
    telegram_id bigint unique, -- optional, for Telegram integration
    username text, -- optional, from Telegram
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

-- Folders for organizing notes (tree structure)
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

-- Tags system
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

-- Notes with rich content and organization
create table if not exists notes (
    id uuid primary key default uuid_generate_v4(),
    user_id uuid not null,
    folder_id uuid,
    title text,
    content text not null,
    content_format text default 'markdown', -- markdown, html, plain
    is_favorite boolean default false,
    is_archived boolean default false,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint notes_user_fk foreign key (user_id)
        references users (id) on delete cascade
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

-- Note tags (many-to-many)
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

-- Projects
create table if not exists projects (
    id uuid primary key default uuid_generate_v4(),
    user_id uuid not null,
    name text not null,
    description text,
    color text,
    deadline timestamptz,
    status text default 'active', -- active, completed, archived
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

-- Tasks with full GTD support
create table if not exists tasks (
    id uuid primary key default uuid_generate_v4(),
    user_id uuid not null,
    project_id uuid,
    parent_task_id uuid, -- for subtasks
    title text not null,
    description text,
    priority text default 'medium' check (priority in ('low', 'medium', 'high', 'critical')),
    status text default 'new' check (status in ('new', 'in_progress', 'waiting', 'completed', 'cancelled')),
    deadline timestamptz,
    estimated_hours decimal(4,1),
    actual_hours decimal(4,1),
    is_recurring boolean default false,
    recurrence_rule text, -- RRULE format
    assigned_to uuid, -- future: assigned to other users
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint tasks_user_fk foreign key (user_id)
        references users (id) on delete cascade
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

-- Task tags (many-to-many)
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

-- Task subtasks (for complex tasks)
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

-- AI Assistant sessions
create table if not exists assistant_sessions (
    id uuid primary key default uuid_generate_v4(),
    user_id uuid not null,
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

-- AI Assistant messages
create table if not exists assistant_messages (
    id uuid primary key default uuid_generate_v4(),
    session_id uuid,
    user_id uuid not null,
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

-- AI Assistant conversation summaries
create table if not exists assistant_conversation_summaries (
    id uuid primary key default uuid_generate_v4(),
    user_id uuid not null,
    telegram_id bigint,
    summary text not null,
    created_at timestamptz not null default now(),
    constraint assistant_conversation_summaries_user_fk foreign key (user_id)
        references users (id) on delete cascade
);

create index if not exists idx_assistant_conversation_summaries_user on assistant_conversation_summaries (user_id);
create index if not exists idx_assistant_conversation_summaries_created on assistant_conversation_summaries (created_at desc);

-- File attachments
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

-- Sleep tracking sessions
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

-- Legacy Telegram support (for backward compatibility)
alter table users add column if not exists telegram_id bigint unique;
alter table users add column if not exists username text;
alter table notes add column if not exists folder_id uuid;
alter table notes add constraint notes_folder_fk foreign key (folder_id) references note_folders (id) on delete set null;
alter table notes add column if not exists telegram_id bigint;
alter table tasks add constraint tasks_project_fk foreign key (project_id) references projects (id) on delete set null;
alter table tasks add constraint tasks_parent_fk foreign key (parent_task_id) references tasks (id) on delete cascade;
alter table tasks add constraint tasks_assigned_fk foreign key (assigned_to) references users (id) on delete set null;
alter table tasks add column if not exists telegram_id bigint;
alter table assistant_sessions add column if not exists telegram_id bigint;
alter table assistant_messages add column if not exists telegram_id bigint;
