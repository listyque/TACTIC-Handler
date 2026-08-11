-- Duplicate user/group membership
SELECT login, login_group, count(*) FROM login_in_group GROUP BY login, login_group HAVING count(*) > 1;

-- Duplicate subscriptions
SELECT message_code, login, category, count(*) FROM subscription GROUP BY message_code, login, category HAVING count(*) > 1;

-- Orphan message logs
SELECT ml.code, ml.message_code FROM message_log ml LEFT JOIN message m ON m.code=ml.message_code WHERE m.code IS NULL;

-- Orphan file rows by snapshot_code
SELECT f.code, f.snapshot_code FROM file f LEFT JOIN snapshot s ON s.code=f.snapshot_code WHERE f.snapshot_code IS NOT NULL AND s.code IS NULL;

-- Duplicate core codes (should normally be prevented by constraints)
SELECT code, count(*) FROM snapshot GROUP BY code HAVING count(*) > 1;
SELECT code, count(*) FROM file GROUP BY code HAVING count(*) > 1;
SELECT code, count(*) FROM task GROUP BY code HAVING count(*) > 1;
