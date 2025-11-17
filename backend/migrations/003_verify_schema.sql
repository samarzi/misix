-- Verification script to check what tables and columns exist
-- Run this to see what's in your database

-- List all tables
SELECT 
    table_name,
    table_type
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- List all columns for each table
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_schema = 'public' 
ORDER BY table_name, ordinal_position;

-- Check for missing columns in notes table
SELECT 
    CASE 
        WHEN EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notes' AND column_name = 'is_favorite') 
        THEN '✅ is_favorite exists'
        ELSE '❌ is_favorite missing'
    END as is_favorite_status,
    CASE 
        WHEN EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notes' AND column_name = 'is_archived') 
        THEN '✅ is_archived exists'
        ELSE '❌ is_archived missing'
    END as is_archived_status,
    CASE 
        WHEN EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notes' AND column_name = 'content_format') 
        THEN '✅ content_format exists'
        ELSE '❌ content_format missing'
    END as content_format_status,
    CASE 
        WHEN EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notes' AND column_name = 'folder_id') 
        THEN '✅ folder_id exists'
        ELSE '❌ folder_id missing'
    END as folder_id_status;

-- Check for missing columns in note_folders table
SELECT 
    CASE 
        WHEN EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'note_folders' AND column_name = 'parent_id') 
        THEN '✅ parent_id exists'
        ELSE '❌ parent_id missing'
    END as parent_id_status,
    CASE 
        WHEN EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'note_folders' AND column_name = 'color') 
        THEN '✅ color exists'
        ELSE '❌ color missing'
    END as color_status;

-- Check for missing columns in tasks table
SELECT 
    CASE 
        WHEN EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'tasks' AND column_name = 'priority') 
        THEN '✅ priority exists'
        ELSE '❌ priority missing'
    END as priority_status,
    CASE 
        WHEN EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'tasks' AND column_name = 'status') 
        THEN '✅ status exists'
        ELSE '❌ status missing'
    END as status_status,
    CASE 
        WHEN EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'tasks' AND column_name = 'deadline') 
        THEN '✅ deadline exists'
        ELSE '❌ deadline missing'
    END as deadline_status;
