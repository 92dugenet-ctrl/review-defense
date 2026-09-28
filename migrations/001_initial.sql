CREATE TABLE IF NOT EXISTS schema_meta (key TEXT PRIMARY KEY,value TEXT NOT NULL);
INSERT INTO schema_meta(key,value) VALUES ('version','1') ON CONFLICT(key) DO UPDATE SET value=EXCLUDED.value;
