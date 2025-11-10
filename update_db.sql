-- Alter tables to add missing columns and constraints
-- Run this after init_db.sql

-- Legacy Telegram support (for backward compatibility)
alter table users add column if not exists telegram_id bigint unique;
alter table users add column if not exists username text;
alter table notes add column if not exists folder_id uuid;
alter table notes add column if not exists telegram_id bigint;
alter table tasks add column if not exists telegram_id bigint;
alter table assistant_sessions add column if not exists telegram_id bigint;
alter table assistant_messages add column if not exists telegram_id bigint;
alter table tasks add column if not exists project_id uuid;
alter table tasks add column if not exists parent_task_id uuid;
alter table tasks add column if not exists assigned_to uuid;
alter table tasks add column if not exists priority text;
alter table tasks add column if not exists status text;
alter table tasks add column if not exists deadline timestamptz;
alter table tasks add column if not exists estimated_hours decimal(4,1);
alter table tasks add column if not exists actual_hours decimal(4,1);
alter table tasks add column if not exists is_recurring boolean;
alter table tasks add column if not exists recurrence_rule text;

-- Add constraints (run after columns are added)
alter table notes add constraint notes_folder_fk foreign key (folder_id) references note_folders (id) on delete set null;
alter table tasks add constraint tasks_project_fk foreign key (project_id) references projects (id) on delete set null;
alter table tasks add constraint tasks_parent_fk foreign key (parent_task_id) references tasks (id) on delete cascade;
alter table tasks add constraint tasks_assigned_fk foreign key (assigned_to) references users (id) on delete set null;
