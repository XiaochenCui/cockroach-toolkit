DROP TABLE IF EXISTS foo;
CREATE TABLE foo (a INT PRIMARY KEY, b STRING);

-- INSERT INTO foo VALUES (1, 'xiaochen_debug_insert');

-- apply the schema change
-- ALTER TABLE foo ADD COLUMN c STRING DEFAULT 'xiaochen_default';

-- show the plan of the schema change
EXPLAIN (DDL) ALTER TABLE foo ADD COLUMN c STRING DEFAULT 'xiaochen_default';

-- show the visualized plan of the schema change
EXPLAIN (DDL, VIZ) ALTER TABLE foo ADD COLUMN c STRING DEFAULT 'xiaochen_default';

-- SELECT * FROM foo;