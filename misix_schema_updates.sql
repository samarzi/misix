-- Extended MISIX Schema Updates
-- Add support for finances, personal data, diary, and assistant personalization

-- =============================================
-- 1. FINANCIAL TRACKER
-- =============================================

-- Expense/Income categories
create table if not exists finance_categories (
    id uuid primary key default uuid_generate_v4(),
    user_id uuid not null,
    name text not null,
    type text not null check (type in ('income', 'expense')),
    color text,
    icon text,
    parent_id uuid, -- for subcategories
    is_default boolean default false,
    sort_order integer default 0,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint finance_categories_user_fk foreign key (user_id)
        references users (id) on delete cascade,
    constraint finance_categories_parent_fk foreign key (parent_id)
        references finance_categories (id) on delete cascade,
    constraint finance_categories_user_name_unique unique (user_id, name, type)
);

drop trigger if exists set_finance_categories_updated_at on finance_categories;
create trigger set_finance_categories_updated_at
    before update on finance_categories
    for each row
    execute procedure trigger_set_timestamp();

create index if not exists idx_finance_categories_user on finance_categories (user_id);
create index if not exists idx_finance_categories_type on finance_categories (user_id, type);

-- Financial transactions (expenses and income)
create table if not exists finance_transactions (
    id uuid primary key default uuid_generate_v4(),
    user_id uuid not null,
    category_id uuid,
    amount decimal(12,2) not null,
    currency text default 'RUB',
    type text not null check (type in ('income', 'expense')),
    description text,
    merchant text, -- where the transaction happened
    payment_method text, -- cash, card, transfer, etc.
    tags text[], -- array of tags
    transaction_date timestamptz not null default now(),
    is_recurring boolean default false,
    recurrence_rule text, -- RRULE for recurring transactions
    receipt_url text, -- link to receipt image
    notes text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint finance_transactions_user_fk foreign key (user_id)
        references users (id) on delete cascade,
    constraint finance_transactions_category_fk foreign key (category_id)
        references finance_categories (id) on delete set null
);

drop trigger if exists set_finance_transactions_updated_at on finance_transactions;
create trigger set_finance_transactions_updated_at
    before update on finance_transactions
    for each row
    execute procedure trigger_set_timestamp();

create index if not exists idx_finance_transactions_user on finance_transactions (user_id);
create index if not exists idx_finance_transactions_category on finance_transactions (category_id);
create index if not exists idx_finance_transactions_date on finance_transactions (user_id, transaction_date);
create index if not exists idx_finance_transactions_type on finance_transactions (user_id, type);

-- =============================================
-- 2. PERSONAL DATA STORAGE (Logins, Passwords, Personal Info)
-- =============================================

-- Personal data categories
create table if not exists personal_data_categories (
    id uuid primary key default uuid_generate_v4(),
    user_id uuid not null,
    name text not null,
    description text,
    color text,
    icon text,
    is_confidential boolean default false, -- for sensitive data
    sort_order integer default 0,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint personal_data_categories_user_fk foreign key (user_id)
        references users (id) on delete cascade,
    constraint personal_data_categories_user_name_unique unique (user_id, name)
);

drop trigger if exists set_personal_data_categories_updated_at on personal_data_categories;
create trigger set_personal_data_categories_updated_at
    before update on personal_data_categories
    for each row
    execute procedure trigger_set_timestamp();

create index if not exists idx_personal_data_categories_user on personal_data_categories (user_id);

-- Personal data entries (logins, passwords, contacts, etc.)
create table if not exists personal_data_entries (
    id uuid primary key default uuid_generate_v4(),
    user_id uuid not null,
    category_id uuid,
    title text not null, -- e.g., "Gmail Account", "Bank Card"
    data_type text not null check (data_type in ('login', 'contact', 'document', 'other')),
    -- Encrypted fields for sensitive data
    login_username text,
    login_password text, -- encrypted
    contact_name text,
    contact_phone text,
    contact_email text,
    document_number text,
    document_expiry date,
    custom_fields jsonb, -- for flexible data storage
    tags text[],
    notes text,
    is_favorite boolean default false,
    is_confidential boolean default false,
    last_accessed timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint personal_data_entries_user_fk foreign key (user_id)
        references users (id) on delete cascade,
    constraint personal_data_entries_category_fk foreign key (category_id)
        references personal_data_categories (id) on delete set null
);

drop trigger if exists set_personal_data_entries_updated_at on personal_data_entries;
create trigger set_personal_data_entries_updated_at
    before update on personal_data_entries
    for each row
    execute procedure trigger_set_timestamp();

create index if not exists idx_personal_data_entries_user on personal_data_entries (user_id);
create index if not exists idx_personal_data_entries_category on personal_data_entries (category_id);
create index if not exists idx_personal_data_entries_type on personal_data_entries (user_id, data_type);

-- =============================================
-- 3. DIARY AND PSYCHOLOGICAL SUPPORT
-- =============================================

-- Mood tracking
create table if not exists mood_entries (
    id uuid primary key default uuid_generate_v4(),
    user_id uuid not null,
    mood_level integer not null check (mood_level >= 1 and mood_level <= 10), -- 1-10 scale
    mood_description text, -- happy, sad, anxious, etc.
    energy_level integer check (energy_level >= 1 and energy_level <= 10),
    stress_level integer check (stress_level >= 1 and stress_level <= 10),
    sleep_hours decimal(4,1),
    notes text,
    factors text[], -- what influenced the mood
    entry_date date not null default current_date,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint mood_entries_user_fk foreign key (user_id)
        references users (id) on delete cascade,
    constraint mood_entries_user_date_unique unique (user_id, entry_date)
);

drop trigger if exists set_mood_entries_updated_at on mood_entries;
create trigger set_mood_entries_updated_at
    before update on mood_entries
    for each row
    execute procedure trigger_set_timestamp();

create index if not exists idx_mood_entries_user on mood_entries (user_id);
create index if not exists idx_mood_entries_date on mood_entries (user_id, entry_date);

-- Diary entries (more detailed than mood)
create table if not exists diary_entries (
    id uuid primary key default uuid_generate_v4(),
    user_id uuid not null,
    title text,
    content text not null,
    entry_type text default 'general' check (entry_type in ('general', 'gratitude', 'reflection', 'dream', 'goal', 'achievement')),
    mood_level integer check (mood_level >= 1 and mood_level <= 10),
    tags text[],
    is_private boolean default false, -- for confidential entries
    entry_date date not null default current_date,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint diary_entries_user_fk foreign key (user_id)
        references users (id) on delete cascade
);

drop trigger if exists set_diary_entries_updated_at on diary_entries;
create trigger set_diary_entries_updated_at
    before update on diary_entries
    for each row
    execute procedure trigger_set_timestamp();

create index if not exists idx_diary_entries_user on diary_entries (user_id);
create index if not exists idx_diary_entries_date on diary_entries (user_id, entry_date);
create index if not exists idx_diary_entries_type on diary_entries (user_id, entry_type);

-- Personal profile data (age, weight, preferences, etc.)
create table if not exists user_profile_data (
    id uuid primary key default uuid_generate_v4(),
    user_id uuid not null,
    data_key text not null, -- 'age', 'weight', 'height', 'favorite_color', etc.
    data_value text,
    data_type text default 'text' check (data_type in ('text', 'number', 'date', 'boolean')),
    is_private boolean default false,
    category text default 'personal', -- personal, preferences, health, etc.
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint user_profile_data_user_fk foreign key (user_id)
        references users (id) on delete cascade,
    constraint user_profile_data_user_key_unique unique (user_id, data_key)
);

drop trigger if exists set_user_profile_data_updated_at on user_profile_data;
create trigger set_user_profile_data_updated_at
    before update on user_profile_data
    for each row
    execute procedure trigger_set_timestamp();

create index if not exists idx_user_profile_data_user on user_profile_data (user_id);
create index if not exists idx_user_profile_data_category on user_profile_data (user_id, category);

-- =============================================
-- 4. HEALTH METRICS
-- =============================================

create table if not exists health_metrics (
    id uuid primary key default uuid_generate_v4(),
    user_id uuid not null,
    metric_type text not null,
    metric_value numeric(12, 4) not null,
    unit text,
    recorded_at timestamptz not null default now(),
    note text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint health_metrics_user_fk foreign key (user_id)
        references users (id) on delete cascade
);

drop trigger if exists set_health_metrics_updated_at on health_metrics;
create trigger set_health_metrics_updated_at
    before update on health_metrics
    for each row
    execute procedure trigger_set_timestamp();

create index if not exists idx_health_metrics_user on health_metrics (user_id);
create index if not exists idx_health_metrics_type on health_metrics (user_id, metric_type);
create index if not exists idx_health_metrics_recorded_at on health_metrics (user_id, recorded_at desc);

-- =============================================
-- 5. ASSISTANT PERSONALIZATION
-- =============================================

-- Assistant personas/characters
create table if not exists assistant_personas (
    id uuid primary key default uuid_generate_v4(),
    name text not null unique,
    display_name text not null,
    description text,
    system_prompt text not null, -- base prompt for this persona
    tone text default 'neutral', -- formal, friendly, motivational, etc.
    language_style text default 'neutral', -- formal, casual, professional
    empathy_level text default 'medium', -- low, medium, high
    motivation_level text default 'medium', -- low, medium, high
    is_active boolean default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

-- Insert default personas
insert into assistant_personas (name, display_name, description, system_prompt, tone, language_style, empathy_level, motivation_level)
values
    ('business', 'Деловой', 'Строгий и эффективный стиль общения', 'Ты - деловой ассистент. Будь краток, точен и профессионален. Фокусируйся на эффективности и результатах.', 'formal', 'professional', 'low', 'medium'),
    ('friendly', 'Дружелюбный', 'Теплый и дружелюбный стиль', 'Ты - дружелюбный помощник. Будь доброжелателен, используй теплое общение, поддерживай позитивный тон.', 'friendly', 'casual', 'high', 'medium'),
    ('motivational', 'Мотивационный', 'Вдохновляющий и мотивирующий', 'Ты - мотивационный коуч. Вдохновляй пользователя на достижения, поддерживай в трудные моменты, помогай развиваться.', 'motivational', 'casual', 'high', 'high'),
    ('calm', 'Спокойный', 'Уравновешенный и медитативный', 'Ты - спокойный и уравновешенный помощник. Говори медленно, предлагай медитации и практики осознанности.', 'calm', 'neutral', 'high', 'low')
on conflict (name) do nothing;

drop trigger if exists set_assistant_personas_updated_at on assistant_personas;
create trigger set_assistant_personas_updated_at
    before update on assistant_personas
    for each row
    execute procedure trigger_set_timestamp();

-- User assistant settings
create table if not exists user_assistant_settings (
    id uuid primary key default uuid_generate_v4(),
    user_id uuid not null,
    current_persona_id uuid,
    voice_enabled boolean default false,
    notifications_enabled boolean default true,
    language text default 'ru',
    timezone text default 'Europe/Moscow',
    working_hours_start time default '09:00',
    working_hours_end time default '18:00',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint user_assistant_settings_user_fk foreign key (user_id)
        references users (id) on delete cascade,
    constraint user_assistant_settings_persona_fk foreign key (current_persona_id)
        references assistant_personas (id) on delete set null,
    constraint user_assistant_settings_user_unique unique (user_id)
);

drop trigger if exists set_user_assistant_settings_updated_at on user_assistant_settings;
create trigger set_user_assistant_settings_updated_at
    before update on user_assistant_settings
    for each row
    execute procedure trigger_set_timestamp();

create index if not exists idx_user_assistant_settings_user on user_assistant_settings (user_id);

-- =============================================
-- 5. EVENT CLASSIFICATION AND AUTOMATION
-- =============================================

-- Event types for automatic classification
create table if not exists event_types (
    id uuid primary key default uuid_generate_v4(),
    name text not null unique,
    display_name text not null,
    description text,
    keywords text[], -- keywords for detection
    ai_prompt text, -- specific prompt for this event type
    default_category text,
    requires_confirmation boolean default false,
    is_active boolean default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

-- Insert default event types
insert into event_types (name, display_name, description, keywords, default_category, requires_confirmation)
values
    ('expense', 'Расход', 'Финансовый расход', array['потратил', 'купил', 'заплатил', 'расход', 'цена'], 'finance', false),
    ('income', 'Доход', 'Финансовый доход', array['получил', 'заработал', 'доход', 'зарплата', 'премия'], 'finance', true),
    ('task', 'Задача', 'Создание задачи', array['сделать', 'задача', 'напомни', 'нужно', 'обязательно'], 'task', false),
    ('note', 'Заметка', 'Создание заметки', array['запомни', 'запиши', 'заметка', 'важное'], 'note', false),
    ('mood', 'Настроение', 'Отслеживание настроения', array['настроение', 'чувствую', 'эмоции', 'mood'], 'diary', false),
    ('login', 'Логин/Пароль', 'Сохранение учетных данных', array['логин', 'пароль', 'аккаунт', 'доступ'], 'personal', true),
    ('contact', 'Контакт', 'Сохранение контакта', array['телефон', 'контакт', 'номер', 'email'], 'personal', false)
on conflict (name) do nothing;

drop trigger if exists set_event_types_updated_at on event_types;
create trigger set_event_types_updated_at
    before update on event_types
    for each row
    execute procedure trigger_set_timestamp();

-- User event processing history (for learning and improvement)
create table if not exists user_event_history (
    id uuid primary key default uuid_generate_v4(),
    user_id uuid not null,
    original_text text not null,
    detected_event_type text,
    confidence_score decimal(3,2), -- 0.00 to 1.00
    was_correct boolean,
    user_feedback text,
    processing_time_ms integer,
    created_at timestamptz not null default now(),
    constraint user_event_history_user_fk foreign key (user_id)
        references users (id) on delete cascade
);

create index if not exists idx_user_event_history_user on user_event_history (user_id);
create index if not exists idx_user_event_history_type on user_event_history (user_id, detected_event_type);

-- =============================================
-- 6. DEFAULT DATA INSERTION
-- =============================================

-- Default finance categories
insert into finance_categories (user_id, name, type, color, icon, is_default, sort_order)
select
    u.id as user_id,
    cat.name,
    cat.type,
    cat.color,
    cat.icon,
    true as is_default,
    cat.sort_order
from users u
cross join (
    values
        ('Продукты', 'expense', '#10b981', 'shopping-cart', 1),
        ('Транспорт', 'expense', '#3b82f6', 'car', 2),
        ('Кафе и рестораны', 'expense', '#f59e0b', 'utensils', 3),
        ('Развлечения', 'expense', '#8b5cf6', 'gamepad', 4),
        ('Здоровье', 'expense', '#ef4444', 'heart', 5),
        ('Одежда', 'expense', '#ec4899', 'shirt', 6),
        ('Коммунальные услуги', 'expense', '#6b7280', 'home', 7),
        ('Зарплата', 'income', '#22c55e', 'dollar-sign', 1),
        ('Фриланс', 'income', '#06b6d4', 'briefcase', 2),
        ('Инвестиции', 'income', '#f97316', 'trending-up', 3)
) as cat(name, type, color, icon, sort_order)
where not exists (
    select 1 from finance_categories fc
    where fc.user_id = u.id and fc.name = cat.name and fc.type = cat.type
);

-- Default personal data categories
insert into personal_data_categories (user_id, name, description, color, icon, is_confidential, sort_order)
select
    u.id as user_id,
    cat.name,
    cat.description,
    cat.color,
    cat.icon,
    cat.is_confidential,
    cat.sort_order
from users u
cross join (
    values
        ('Работа', 'Рабочие аккаунты и доступы', '#3b82f6', 'briefcase', true, 1),
        ('Личные', 'Личные аккаунты', '#10b981', 'user', true, 2),
        ('Банки', 'Банковские карты и счета', '#ef4444', 'credit-card', true, 3),
        ('Документы', 'Паспорт, права, документы', '#f59e0b', 'file-text', true, 4),
        ('Контакты', 'Важные контакты', '#8b5cf6', 'phone', false, 5)
) as cat(name, description, color, icon, is_confidential, sort_order)
where not exists (
    select 1 from personal_data_categories pdc
    where pdc.user_id = u.id and pdc.name = cat.name
);

-- Set default assistant settings for existing users
insert into user_assistant_settings (user_id)
select id from users u
where not exists (
    select 1 from user_assistant_settings uas where uas.user_id = u.id
);

-- Fix for folder_id error
DO $$
BEGIN
    CREATE TABLE IF NOT EXISTS note_folders (
        id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
        user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name='notes' AND column_name='folder_id'
    ) THEN
        ALTER TABLE notes ADD COLUMN folder_id uuid;
    END IF;

    ALTER TABLE notes 
        DROP CONSTRAINT IF EXISTS notes_folder_fk,
        ADD CONSTRAINT notes_folder_fk FOREIGN KEY (folder_id) 
            REFERENCES note_folders(id) ON DELETE SET NULL;
END $$;
