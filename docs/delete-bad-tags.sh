sqlite3 searchy.db <<'EOF'
CREATE TEMP TABLE temp_tags (value TEXT);
.import --csv bad-tags.txt temp_tags
DELETE FROM link_tags WHERE tag_id IN (
    SELECT id FROM tags WHERE name IN (SELECT value FROM temp_tags)
);
DELETE FROM tags WHERE name IN (SELECT value FROM temp_tags);
DROP TABLE temp_tags;
EOF
