---
name: "@tank/relational-db-mastery"
description: |
  Relational database performance optimization for PostgreSQL and MySQL.
  Covers indexing strategies (B-tree, GIN, GiST, BRIN, partial, expression,
  covering, composite), query optimization (JOINs, CTEs, pagination, N+1),
  EXPLAIN ANALYZE interpretation, schema design for performance, PostgreSQL
  tuning (VACUUM, autovacuum, connection pooling, pg_stat_statements),
  MySQL/InnoDB tuning, and monitoring diagnostics.

  Synthesizes Winand (SQL Performance Explained), Petrov (Database Internals),
  Karwin (SQL Antipatterns), Schwartz (High Performance MySQL), Kleppmann
  (Designing Data-Intensive Applications), and PostgreSQL/MySQL documentation.

  Trigger phrases: "slow query", "query optimization", "database performance",
  "index", "indexing strategy", "EXPLAIN ANALYZE", "query plan",
  "schema design", "normalization", "denormalization", "B-tree", "GIN index",
  "composite index", "covering index", "partial index", "N+1 query",
  "pagination", "keyset pagination", "cursor pagination", "connection pool",
  "PgBouncer", "VACUUM", "autovacuum", "table bloat", "dead tuples",
  "cache hit ratio", "PostgreSQL tuning", "MySQL tuning", "InnoDB",
  "foreign key index", "missing index", "over-indexing", "database schema",
  "data types", "partitioning", "pg_stat_statements", "slow query log",
  "JOINs", "subquery vs CTE", "query rewriting", "database optimization",
  "SQL performance", "database design", "relational database"
---
# Relational Database Mastery

## Core Philosophy

1. **Measure before optimizing** — Run EXPLAIN ANALYZE before changing anything. Intuition about query performance is unreliable.
2. **Index for queries, not columns** — Design indexes based on actual query patterns, not schema structure.
3. **Normalize first, denormalize with evidence** — Start with 3NF. Denormalize only when measurements prove a JOIN is the bottleneck.
4. **The database is not a black box** — Understand the planner's decisions. Read query plans. Monitor cache hit ratios.
5. **PostgreSQL and MySQL are different engines** — Tuning that works for one may hurt the other. Know which you're targeting.

## Quick-Start: Common Problems

### "My query is slow"

1. Get the query → Run `EXPLAIN (ANALYZE, BUFFERS)` on it
2. Read the plan bottom-to-top → Find the node with highest actual time
3. Is it a Seq Scan on a large table? → Add an index (see `references/indexing-strategies.md`)
4. Are row estimates wildly wrong? → Run `ANALYZE` on the table
5. Is it a disk-bound Sort? → Increase `work_mem` or add matching index
→ See `references/explain-analyze.md` for full plan reading guide

### "Which index should I create?"

1. What's the query pattern? Equality, range, full-text, JSONB, geometric?
2. Apply the Index Type Selection table → B-tree, GIN, GiST, or BRIN
3. Composite index? → Apply E-R-S rule: Equality columns → Range columns → Sort columns
4. Large table, skewed data? → Use partial index
5. Need index-only scans? → Use covering index with INCLUDE
→ See `references/indexing-strategies.md`

### "Database is generally slow"

1. Check cache hit ratio → Below 99%? Increase `shared_buffers`
2. Check active connections → Near max? Add connection pooling
3. Check dead tuple ratio → Above 20%? Tune autovacuum
4. Check `pg_stat_statements` → Find top queries by total time
5. Check for lock contention → Long-running transactions blocking others
→ See `references/monitoring-diagnostics.md` and `references/postgresql-tuning.md`

### "Should I normalize or denormalize?"

1. Is this a new schema? → Normalize to 3NF
2. Are JOINs proven slow via EXPLAIN? → Consider denormalization
3. Is it read-heavy with complex aggregations? → Materialized views
4. Is it write-heavy with consistency needs? → Stay normalized
→ See `references/schema-design.md`

## Decision Trees

### Index Type Selection

| Query Pattern | Index Type | Example |
|---|---|---|
| Equality (`=`) | B-tree | `WHERE status = 'active'` |
| Range (`<`, `>`, `BETWEEN`) | B-tree | `WHERE created_at > '2024-01-01'` |
| Pattern match (`LIKE 'prefix%'`) | B-tree | `WHERE name LIKE 'John%'` |
| Full-text search | GIN | `WHERE to_tsvector('english', body) @@ query` |
| JSONB containment | GIN | `WHERE metadata @> '{"type":"admin"}'` |
| Array contains | GIN | `WHERE tags @> ARRAY['python']` |
| Geometric/spatial | GiST | `WHERE ST_DWithin(geom, point, 1000)` |
| Range overlap | GiST | `WHERE tsrange @> now()` |
| Large time-series table | BRIN | `WHERE created_at > '2024-01-01'` (billions of rows) |

### Query Pattern Selection

| Situation | Use | Avoid |
|---|---|---|
| Direct table relationship | JOIN | Correlated subquery |
| Existence check | `EXISTS (SELECT 1 ...)` | `IN (SELECT ...)` on large sets |
| Multi-step transformation | CTE (PG 12+ inlines) | Nested subqueries |
| Top-N per group | `LATERAL JOIN` or `ROW_NUMBER()` | Correlated subquery per row |
| Large dataset pagination | Keyset/cursor pagination | `OFFSET` on large offsets |
| Bulk data loading | `COPY` (PG) / `LOAD DATA` (MySQL) | Individual INSERT statements |

### PostgreSQL vs MySQL Tuning

| Concern | PostgreSQL | MySQL |
|---|---|---|
| Main memory setting | `shared_buffers` (25% RAM) | `innodb_buffer_pool_size` (70-80% RAM) |
| Dead row cleanup | VACUUM / autovacuum | InnoDB purge thread (automatic) |
| Connection overhead | Heavy (process per conn) → use PgBouncer | Light (thread per conn) |
| Slow query identification | `pg_stat_statements` | Slow query log + `pt-query-digest` |
| Online index creation | `CREATE INDEX CONCURRENTLY` | `ALTER TABLE ... ADD INDEX` (online by default) |
| SSD optimization | `random_page_cost = 1.1` | `innodb_io_capacity = 2000+` |

## Anti-Patterns Quick Reference

| Anti-Pattern | Problem | Fix |
|---|---|---|
| No index on foreign keys | Slow JOINs, slow CASCADE deletes | Always index FKs |
| `SELECT *` everywhere | Extra I/O, blocks index-only scans | Select only needed columns |
| `WHERE function(column)` | Kills index usage | Expression index or rewrite query |
| `OFFSET 10000 LIMIT 20` | Scans and discards 10000 rows | Keyset pagination |
| N+1 queries in ORM | 1 + N round trips to database | Eager loading or batch fetch |
| `FLOAT` for money | Rounding errors | `NUMERIC(precision, scale)` |
| UUID v4 primary keys | Random B-tree inserts, fragmentation | UUIDv7 or BIGSERIAL + public UUID |
| Over-indexing | Write amplification, disk waste | Audit with `pg_stat_user_indexes` |
| Skipping `ANALYZE` | Stale statistics, bad plans | Run after bulk data changes |

## Reference Files

| File | Contents |
|------|----------|
| `references/indexing-strategies.md` | All index types, selection decision tree, composite index column order (E-R-S rule), GIN/GiST/BRIN deep dives, anti-patterns, PG vs MySQL differences |
| `references/query-optimization.md` | JOIN optimization, subquery vs CTE vs JOIN, N+1 problem, pagination strategies, batch operations, window functions, query rewriting |
| `references/explain-analyze.md` | Reading EXPLAIN output, scan types, join types, cost model, red flags, estimation errors, MySQL differences, optimization workflow |
| `references/schema-design.md` | Normalization/denormalization, data type selection (UUID vs serial, JSONB vs columns), partitioning, temporal patterns, schema anti-patterns |
| `references/postgresql-tuning.md` | Memory config, SSD settings, VACUUM/autovacuum, connection pooling (PgBouncer), lock management, pg_stat_statements, WAL tuning |
| `references/mysql-tuning.md` | InnoDB architecture, buffer pool, flush settings, slow query log, optimizer hints, character sets, replication, PG vs MySQL comparison |
| `references/monitoring-diagnostics.md` | Key metrics dashboard, diagnostic queries (PG + MySQL), cache hit ratio, index usage, table bloat, alerting thresholds, diagnostic workflow |
