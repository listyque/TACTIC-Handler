-- TACTIC live schema inventory.
-- Run in the sthpw database and separately in every project database.

-- 1. Physical tables and columns.
SELECT
    table_schema,
    table_name,
    ordinal_position,
    column_name,
    data_type,
    udt_name,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
ORDER BY table_schema, table_name, ordinal_position;

-- 2. Indexes.
SELECT
    schemaname AS table_schema,
    tablename AS table_name,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY schemaname, tablename, indexname;

-- 3. Primary/unique/foreign/check constraints.
SELECT
    tc.table_schema,
    tc.table_name,
    tc.constraint_name,
    tc.constraint_type,
    kcu.column_name,
    ccu.table_schema AS foreign_table_schema,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints tc
LEFT JOIN information_schema.key_column_usage kcu
    ON tc.constraint_schema = kcu.constraint_schema
   AND tc.constraint_name = kcu.constraint_name
LEFT JOIN information_schema.constraint_column_usage ccu
    ON tc.constraint_schema = ccu.constraint_schema
   AND tc.constraint_name = ccu.constraint_name
WHERE tc.table_schema NOT IN ('pg_catalog', 'information_schema')
ORDER BY tc.table_schema, tc.table_name, tc.constraint_name, kcu.ordinal_position;

-- 4. Approximate row counts; useful for identifying live/unused tables without COUNT(*).
SELECT
    n.nspname AS table_schema,
    c.relname AS table_name,
    c.reltuples::bigint AS estimated_rows
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE c.relkind = 'r'
  AND n.nspname NOT IN ('pg_catalog', 'information_schema')
ORDER BY n.nspname, c.relname;

-- 5. Logical search-type registry. Run in the sthpw DB.
SELECT
    code,
    search_type,
    namespace,
    database,
    table_name,
    class_name,
    schema,
    title,
    description
FROM search_object
ORDER BY search_type;

-- 6. Registered types whose physical location must be checked in the DB named by `database`.
-- Export query 5 and compare table_name/schema with queries 1-4 from each target DB.
