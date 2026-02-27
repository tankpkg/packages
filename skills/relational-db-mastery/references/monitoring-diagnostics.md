# Monitoring and Diagnostics

Sources: PostgreSQL documentation, MySQL documentation, Percona monitoring best practices

Covers: key metrics, diagnostic queries, alerting thresholds, table bloat, cache efficiency, index usage, slow query identification.

## Key Metrics Dashboard

The following metrics represent the primary health indicators for a relational database system. These should be monitored via automated tooling and visualized in a central dashboard.

| Metric | Healthy | Warning | Critical | How to Check |
| :--- | :--- | :--- | :--- | :--- |
| Cache hit ratio | >99% | 95-99% | <95% | pg_stat_database / Innodb_buffer_pool_read_requests |
| Transaction rate | Baseline | 2x baseline | 5x baseline | pg_stat_database (xact_commit + xact_rollback) |
| Active connections | <70% max | 70-90% max | >90% max | pg_stat_activity / SHOW STATUS LIKE 'Threads_connected' |
| Dead tuples ratio | <10% | 10-20% | >20% | pg_stat_user_tables (n_dead_tup / n_live_tup) |
| Replication lag | <1s | 1-10s | >10s | pg_stat_replication / SHOW SLAVE STATUS |
| Disk usage growth | Predictable | Accelerating | Runaway | pg_database_size() / Filesystem monitoring |
| Long-running queries | <5min | 5-30min | >30min | pg_stat_activity / SHOW PROCESSLIST |
| Lock waits | Rare | Occasional | Frequent | pg_locks / information_schema.innodb_lock_waits |

## PostgreSQL Diagnostic Queries

PostgreSQL provides a wealth of information through its system statistics views (the `pg_stat` and `pg_statio` families).

### Cache Hit Ratio
The cache hit ratio measures how often the database finds the required data in memory (shared buffers) versus having to read from the filesystem.

```sql
SELECT
  sum(heap_blks_read) as heap_read,
  sum(heap_blks_hit) as heap_hit,
  round(sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read))::numeric, 4) as ratio
FROM pg_statio_user_tables;
```
-- Target: > 0.99 (99%)
-- If ratio is consistently below 99%, the working set does not fit in memory.
-- Investigation: Identify queries with high "blocks read" using pg_stat_statements.
-- Action: Increase shared_buffers or optimize index usage to reduce IOPS requirements.

### Index Usage Statistics
Frequent sequential scans on large tables often indicate missing indexes or queries that bypass existing indexes.

```sql
SELECT
  schemaname,
  relname,
  seq_scan,
  idx_scan,
  round(100.0 * idx_scan / NULLIF(seq_scan + idx_scan, 0), 1) as idx_pct,
  n_live_tup
FROM pg_stat_user_tables
WHERE seq_scan + idx_scan > 100
  AND n_live_tup > 10000
ORDER BY idx_pct ASC NULLS FIRST
LIMIT 20;
```
-- Target: idx_pct should be close to 100% for high-traffic tables.
-- Investigation: Use EXPLAIN ANALYZE on queries targeting tables with low idx_pct.
-- Action: Add missing indexes or rewrite queries to allow index usage (e.g., avoid leading wildcards).

### Unused Indexes
Indexes consume disk space and slow down INSERT/UPDATE/DELETE operations. Removing unused indexes is a core maintenance task.

```sql
SELECT
  schemaname,
  relname,
  indexrelname AS index_name,
  idx_scan,
  pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
WHERE idx_scan = 0
  AND indexrelname NOT LIKE '%_pkey'
  AND indexrelname NOT LIKE '%_unique%'
ORDER BY pg_relation_size(indexrelid) DESC;
```
-- Note: Check that the index hasn't been recently created (verify pg_stat_user_indexes.last_idx_scan).
-- Note: Some unique constraints are enforced via indexes; do not drop those required for integrity.
-- Action: Drop indexes with zero scans after verifying they aren't used for rare but critical reporting.

### Table Bloat Detection
Bloat occurs when autovacuum cannot keep up with updates and deletes, leaving "holes" in data pages that increase disk usage and slow down scans.

```sql
SELECT
  schemaname,
  relname,
  n_live_tup,
  n_dead_tup,
  round(100.0 * n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0), 1) as dead_pct,
  last_vacuum,
  last_autovacuum,
  last_analyze,
  last_autoanalyze
FROM pg_stat_user_tables
WHERE n_dead_tup > 1000
ORDER BY n_dead_tup DESC
LIMIT 20;
```
-- Threshold: dead_pct > 20% on large tables suggests autovacuum issues.
-- Investigation: Check if long-running transactions are preventing vacuum from reclaiming space.
-- Action: Tune autovacuum parameters (e.g., autovacuum_vacuum_scale_factor) or run manual VACUUM ANALYZE.

### Active Queries and Locks
Identifying queries that are currently consuming resources or blocking other sessions.

```sql
-- View all active queries and their duration
SELECT
  pid,
  now() - pg_stat_activity.query_start AS duration,
  query,
  state,
  wait_event_type,
  wait_event
FROM pg_stat_activity
WHERE state != 'idle'
  AND query NOT ILIKE '%pg_stat_activity%'
ORDER BY duration DESC
LIMIT 10;

-- Identify blocked and blocking processes
SELECT
  blocked.pid AS blocked_pid,
  blocked.query AS blocked_query,
  blocking.pid AS blocking_pid,
  blocking.query AS blocking_query,
  now() - blocked.query_start AS blocked_duration
FROM pg_stat_activity blocked
JOIN pg_locks bl ON bl.pid = blocked.pid AND NOT bl.granted
JOIN pg_locks gl ON gl.pid != blocked.pid AND gl.locktype = bl.locktype
  AND gl.database IS NOT DISTINCT FROM bl.database
  AND gl.relation IS NOT DISTINCT FROM bl.relation
  AND gl.granted
JOIN pg_stat_activity blocking ON blocking.pid = gl.pid
ORDER BY blocked_duration DESC;
```
-- Investigation: Look for 'ClientRead' wait events (app waiting) vs 'Lock' wait events (DB contention).
-- Action: Terminate blocking PIDs if necessary using `SELECT pg_terminate_backend(pid)`.

### Database and Table Sizes
Tracking physical storage usage to prevent disk exhaustion.

```sql
-- Overall database sizes
SELECT
  datname,
  pg_size_pretty(pg_database_size(datname)) as size,
  pg_database_size(datname) as size_bytes
FROM pg_database
ORDER BY size_bytes DESC;

-- Detailed table size breakdown
SELECT
  schemaname,
  relname,
  pg_size_pretty(pg_total_relation_size(relid)) as total_size,
  pg_size_pretty(pg_relation_size(relid)) as table_size,
  pg_size_pretty(pg_total_relation_size(relid) - pg_relation_size(relid)) as index_size,
  pg_total_relation_size(relid) as total_bytes
FROM pg_stat_user_tables
ORDER BY total_bytes DESC
LIMIT 20;
```
-- Investigation: Compare total_size vs table_size. High index_size may indicate over-indexing.

### Top Queries by Resource Consumption
Requires the `pg_stat_statements` extension. This is the most effective way to find queries that need optimization.

```sql
SELECT
  query,
  calls,
  total_exec_time,
  min_exec_time,
  max_exec_time,
  mean_exec_time,
  stddev_exec_time,
  rows,
  100.0 * total_exec_time / sum(total_exec_time) OVER () AS prop_total_time
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 10;
```
-- Investigation: High `mean_exec_time` indicates slow queries. High `calls` with moderate `mean_exec_time` indicates "death by a thousand cuts."
-- Action: Focus optimization efforts on queries with the highest `prop_total_time`.

### Checkpoint and Background Writer Statistics
Monitoring how data is flushed to disk.

```sql
SELECT
  checkpoints_timed,
  checkpoints_req,
  checkpoint_write_time,
  checkpoint_sync_time,
  buffers_checkpoint,
  buffers_clean,
  maxwritten_clean,
  buffers_backend,
  buffers_alloc
FROM pg_stat_bgwriter;
```
-- Investigation: If `checkpoints_req` is high relative to `checkpoints_timed`, increase `max_wal_size`.
-- Investigation: High `buffers_backend` suggests that backends are doing the work the bgwriter should do; increase `bgwriter_lru_maxpages`.

### Connection Statistics
```sql
SELECT
  state,
  count(*),
  round(100.0 * count(*) / (SELECT setting::int FROM pg_settings WHERE name = 'max_connections'), 1) as pct_of_max
FROM pg_stat_activity
GROUP BY state
ORDER BY count DESC;
```
-- Investigation: High number of "idle" connections may indicate a connection leak in the application.
-- Action: Use a connection pooler like PgBouncer if connections frequently exceed 100.

## MySQL Diagnostic Queries

MySQL diagnostics primarily utilize the `INFORMATION_SCHEMA` and `PERFORMANCE_SCHEMA` databases.

### InnoDB Buffer Pool Hit Ratio
The Buffer Pool is MySQL's most important memory structure.

```sql
SELECT
  (SELECT variable_value FROM performance_schema.global_status WHERE variable_name = 'Innodb_buffer_pool_read_requests') AS read_requests,
  (SELECT variable_value FROM performance_schema.global_status WHERE variable_name = 'Innodb_buffer_pool_reads') AS disk_reads,
  1 - (
    (SELECT variable_value FROM performance_schema.global_status WHERE variable_name = 'Innodb_buffer_pool_reads') /
    (SELECT variable_value FROM performance_schema.global_status WHERE variable_name = 'Innodb_buffer_pool_read_requests')
  ) AS hit_ratio;
```
-- Target: > 0.99
-- Action: Increase `innodb_buffer_pool_size` if ratio is low and memory is available.

### Table and Index Sizes
```sql
SELECT
  table_schema,
  table_name,
  ROUND(data_length / 1024 / 1024, 2) AS data_mb,
  ROUND(index_length / 1024 / 1024, 2) AS index_mb,
  ROUND((data_length + index_length) / 1024 / 1024, 2) AS total_mb,
  table_rows
FROM information_schema.tables
WHERE table_schema NOT IN ('mysql', 'information_schema', 'performance_schema', 'sys')
ORDER BY (data_length + index_length) DESC
LIMIT 20;
```
-- Investigation: Find tables with index_mb > data_mb; these are likely over-indexed.

### Unused Indexes (MySQL)
MySQL tracks index usage in the Performance Schema.

```sql
SELECT
  object_schema,
  object_name,
  index_name,
  count_star AS total_ops,
  count_read,
  count_write
FROM performance_schema.table_io_waits_summary_by_index_usage
WHERE index_name IS NOT NULL
  AND count_read = 0
  AND object_schema NOT IN ('mysql', 'performance_schema')
ORDER BY count_write DESC;
```
-- Action: Evaluate if indexes with 0 reads can be safely removed to improve write performance.

### Active Threads and Processlist
```sql
SELECT
  id,
  user,
  host,
  db,
  command,
  time,
  state,
  info AS query
FROM information_schema.processlist
WHERE command != 'Sleep'
ORDER BY time DESC;
```
-- Investigation: Look for many threads in the 'Locked' or 'Sending data' states.

## Diagnostic Workflow

When troubleshooting database performance issues, follow this structured approach to move from symptoms to root causes.

1. **Verify Scope**: Is the problem affecting all queries (system-wide) or specific ones?
   - If specific: Collect the SQL and execution plan (EXPLAIN ANALYZE).
   - If system-wide: Proceed to resource analysis.

2. **Resource Saturation**: Check OS-level metrics (CPU, RAM, Disk I/O, Network).
   - High CPU: Likely missing indexes or excessive sorting.
   - High I/O: Low cache hit ratio or inefficient full table scans.
   - Memory pressure: Swapping will destroy DB performance.

3. **Cache Efficiency**: Run the Cache Hit Ratio query.
   - If < 99%: Memory is insufficient for the working set. Optimize queries to touch fewer blocks or increase memory.

4. **Connection Health**: Check active connection counts against `max_connections`.
   - If near limit: Check for application connection leaks or slow query pile-up.

5. **Concurrency and Locking**: Check for blocked processes.
   - Look for long-running transactions that might be holding locks.
   - Review application code for "User interaction inside transaction" anti-patterns.

6. **Vacuum/Maintenance Health**: Check dead tuple ratios and bloat.
   - If dead tuples > 20%: Autovacuum is failing. This leads to massive I/O overhead.

7. **Slow Query Log / pg_stat_statements**: Identify the top 5 queries by total time.
   - Optimizing the single most expensive query often provides more relief than dozens of smaller optimizations.

8. **Disk I/O Latency**: If hardware supports it, check I/O wait times.
   - If high despite low volume: Disk failure or SAN congestion.

## Alerting Thresholds

Set thresholds to trigger alerts before performance degradation becomes critical.

| Metric | Alert Level | Threshold | Action |
| :--- | :--- | :--- | :--- |
| Cache hit ratio | Warning | <99% | Increase shared_buffers / pool size |
| Cache hit ratio | Critical | <95% | Immediate memory tuning / Query optimization |
| Connections | Warning | >70% max | Investigate connection leaks or scaling needs |
| Connections | Critical | >90% max | Emergency: add pooling or scale up |
| Dead tuples | Warning | >10% | Tune autovacuum for specific heavy tables |
| Dead tuples | Critical | >30% | Manual VACUUM, investigate long transactions |
| Transaction ID age | Warning | >200M | Monitor autovacuum_freeze_max_age |
| Transaction ID age | Critical | >1B | Emergency: Manual VACUUM FREEZE to avoid wrap-around |
| Replication lag | Warning | >10s | Check replica resources and network throughput |
| Replication lag | Critical | >60s | Investigate WAL generation rate vs replay speed |
| Long queries | Warning | >5min | Review query plan and application intent |
| Long queries | Critical | >30min | Consider automated termination of rogue queries |
| Disk Free Space | Warning | <15% | Investigate bloat or log growth |
| Disk Free Space | Critical | <5% | Immediate capacity increase or cleanup |
