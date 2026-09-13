-- Run in a project DB.
-- Duplicate unconditional naming rules for the same selection dimensions.
SELECT search_type, snapshot_type, context, checkin_type, count(*)
FROM spt_naming
WHERE COALESCE(condition,'') = '' AND COALESCE(s_status,'') <> 'retired'
GROUP BY search_type, snapshot_type, context, checkin_type
HAVING count(*) > 1;

-- Process config rows without a corresponding pipeline code.
SELECT p.code, p.pipeline_code, p.process
FROM spt_process p LEFT JOIN spt_pipeline pl ON pl.code=p.pipeline_code
WHERE pl.code IS NULL AND COALESCE(p.s_status,'') <> 'retired';

-- Duplicate widget configs at identical precedence coordinates.
SELECT search_type, view, category, login, count(*)
FROM spt_widget_config
WHERE COALESCE(s_status,'') <> 'retired'
GROUP BY search_type, view, category, login
HAVING count(*) > 1;
