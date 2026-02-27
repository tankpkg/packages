# PostgreSQL Tuning

Sources: Petrov (Database Internals), PostgreSQL documentation, Percona best practices

Covers: memory config, VACUUM/autovacuum, connection pooling, lock management, pg_stat_statements, WAL tuning.

PostgreSQL performance tuning requires a holistic approach that considers hardware, operating system settings, and the database engine itself. The following reference provides actionable configuration changes and operational strategies for modern production environments.

## Memory Configuration

Memory management in PostgreSQL is split between shared memory (used for caching data) and local memory (used for query execution). Misconfiguration of these parameters is the leading cause of "out of memory" (OOM) kills or severe disk thrashing.

| Parameter | Purpose | Setting Rule |
| :--- | :--- | :--- |
| shared_buffers | The primary page cache for data. | 25% of total system RAM for most workloads. |
| work_mem | Memory for sorts and hash joins. | RAM / (max_connections * 4), typically 16MB-256MB. |
| maintenance_work_mem | Memory for VACUUM and index creation. | 256MB-2GB; higher speeds up maintenance. |
| effective_cache_size | Hint for the query planner. | 50% to 75% of total system RAM. |
| wal_buffers | Buffer for Write Ahead Log. | Usually 64MB; auto-tuned by shared_buffers. |
| temp_buffers | Memory for temporary tables. | 8MB-64MB per session. |

### The work_mem Multiplier Effect
A common mistake is setting `work_mem` too high based on the number of connections. It is critical to understand that `work_mem` is allocated per-operation, not per-connection. A single complex query involving multiple sorts, hash joins, and bitmap heap scans can allocate `work_mem` many times over.

Example:
If `work_mem` is 64MB and a query has 4 sort operations and 2 hash joins, that single query can consume 384MB of RAM. If 100 connections execute this query simultaneously, the system will likely trigger the OOM killer.

### Shared Buffers vs OS Cache
PostgreSQL relies heavily on the operating system's file system cache. While `shared_buffers` is the internal cache, `effective_cache_size` tells the planner how much total memory is available for caching (shared_buffers + OS cache). Setting this correctly prevents the planner from choosing expensive disk scans when the data is likely in RAM.

### Huge Pages and Memory Efficiency
On Linux systems with large amounts of RAM (64GB+), using Huge Pages can reduce the overhead of managing memory page tables.
- **huge_pages = try** (default): Uses huge pages if available.
- **huge_pages = on**: Recommended for production to ensure performance consistency.
- **huge_pages = off**: Only for small dev environments.

## Operating System Level Tuning

Before tuning PostgreSQL parameters, the underlying OS must be configured to support a high-performance database workload.

### Kernel Parameters (sysctl.conf)
| Parameter | Value | Why |
| :--- | :--- | :--- |
| vm.swappiness | 1 or 10 | Discourage swapping database memory to disk. |
| vm.overcommit_memory | 2 | Prevent the OS from overcommitting RAM (prevents OOM kills). |
| vm.overcommit_ratio | 90 | Percentage of RAM to consider for overcommit. |
| vm.dirty_background_ratio | 5 | Start background writes early to avoid I/O spikes. |
| vm.dirty_ratio | 15 | Force sync when 15% of memory is dirty. |

### Transparent Huge Pages (THP)
Transparent Huge Pages should be **disabled** for PostgreSQL. THP can cause unpredictable latency spikes and "stuttering" during memory allocation.
```bash
echo never > /sys/kernel/mm/transparent_hugepage/enabled
echo never > /sys/kernel/mm/transparent_hugepage/defrag
```

## SSD-Optimized Settings

Modern PostgreSQL deployments should almost always run on SSD/NVMe storage. The default configuration, however, still assumes rotating platters (HDDs). These settings must be updated to leverage the low latency and high IOPS of solid-state storage.

| Parameter | HDD Default | SSD Setting | Why |
| :--- | :--- | :--- | :--- |
| random_page_cost | 4.0 | 1.1 | SSD random reads are nearly as fast as sequential. |
| seq_page_cost | 1.0 | 1.0 | Baseline for sequential scans. |
| effective_io_concurrency | 1 | 200 | SSDs handle parallel I/O requests effectively. |
| max_worker_processes | 8 | Match CPU Cores | Allows more parallel workers for I/O tasks. |

Lowering `random_page_cost` is the most impactful change for SSDs. At the default of 4.0, the planner often avoids index scans in favor of sequential scans because it overestimates the cost of random seeks. Setting it to 1.1 encourages the planner to use indexes more aggressively.

## VACUUM Deep Dive

PostgreSQL uses Multi-Version Concurrency Control (MVCC). When a row is updated or deleted, the old version is not immediately removed from disk. It is marked as "dead" (a dead tuple). `VACUUM` is the mechanism that reclaims this space.

### Mechanics of Vacuuming
- **Dead Tuple Reclamation:** Identifies rows no longer visible to any active transaction.
- **Visibility Map Update:** Marks pages that contain no dead tuples so index-only scans can skip checking the heap.
- **Freeze Transaction IDs:** Prevents Transaction ID wraparound (see below).
- **Statistics Update:** When run with `ANALYZE`, updates the planner's view of data distribution.

### Comparison of VACUUM Operations

| Operation | Locks | Reclaims Space | Use Case |
| :--- | :--- | :--- | :--- |
| VACUUM | No lock (ShareUpdateExclusive) | Marks space reusable. | Standard maintenance. |
| VACUUM ANALYZE | No lock (ShareUpdateExclusive) | Marks space + updates stats. | Daily maintenance. |
| VACUUM FULL | AccessExclusive (Blocks all) | Rewrites table, shrinks file. | Extreme bloat recovery. |

**Important:** `VACUUM FULL` should be avoided in production. It creates a complete copy of the table, requiring double the disk space and blocking all reads and writes to the table until it completes.

### Index Bloat
Indices can also suffer from bloat. While `VACUUM` reclaims space in the heap (table), it is less effective at shrinking B-Tree indices.
- **REINDEX TABLE CONCURRENTLY**: Rebuilds the index without blocking writes.
- **pg_repack**: A third-party tool often used to reclaim table and index space without heavy locks.

## Autovacuum Tuning

Autovacuum is a background process that automatically triggers VACUUM and ANALYZE operations. On high-churn systems, the default settings are often too conservative, leading to "table bloat" (where files grow indefinitely because dead space isn't reclaimed fast enough).

### Global Tuning Parameters

| Parameter | Default | Tuning for High Load |
| :--- | :--- | :--- |
| autovacuum_max_workers | 3 | 5-8 on systems with many tables. |
| autovacuum_naptime | 1min | 15s to 30s to check for work more often. |
| autovacuum_vacuum_scale_factor | 0.2 | 0.05 (trigger vacuum at 5% change). |
| autovacuum_analyze_scale_factor | 0.1 | 0.02 (trigger analyze at 2% change). |
| autovacuum_vacuum_cost_limit | 200 | 1000+ (gives workers more "budget" to work). |
| autovacuum_vacuum_cost_delay | 2ms | 0ms or 2ms (reduces throttling). |

### Per-Table Tuning
For very large tables (e.g., audit logs or message queues), the 20% default scale factor is useless. A table with 100 million rows would require 20 million deletions before a vacuum is triggered. This must be tuned per-table:

```sql
-- Target high-churn tables with aggressive vacuuming
ALTER TABLE order_status_history SET (
  autovacuum_vacuum_scale_factor = 0.01,
  autovacuum_analyze_scale_factor = 0.005,
  autovacuum_vacuum_cost_limit = 1000
);
```

## Transaction ID Wraparound Prevention

PostgreSQL uses 32-bit integers for transaction IDs (XIDs), providing approximately 4 billion IDs. Because of MVCC, the engine must "freeze" old rows to indicate they are visible to all future transactions. If the "oldest" unfrozen XID gets too far behind the "current" XID, the database will eventually stop accepting commands to prevent data corruption.

### Monitoring Wraparound Risk
Execute the following query to identify databases approaching the limit:

```sql
SELECT 
    datname, 
    age(datfrozenxid) AS xid_age,
    2147483648 - age(datfrozenxid) AS remaining_until_shutdown
FROM pg_database
ORDER BY xid_age DESC;
```

### Critical Thresholds
- **200 Million:** Autovacuum becomes more aggressive (starts "anti-wraparound" workers).
- **1 Billion:** Warning messages start appearing in logs.
- **2 Billion:** PostgreSQL goes into read-only mode or shuts down to prevent XID wraparound.

## Connection Pooling

PostgreSQL's process-per-connection architecture is robust but resource-intensive. Each connection consumes 5MB-10MB of overhead. High connection counts lead to context switching and memory exhaustion.

### PgBouncer Modes

| Mode | Behavior | Best For |
| :--- | :--- | :--- |
| Session | Connection tied to client for its lifetime. | Legacy apps, LISTEN/NOTIFY. |
| Transaction | Connection returned to pool after `COMMIT`. | 99% of web applications. |
| Statement | Connection returned after every query. | Highly specialized, no transactions. |

### Configuration Example (PgBouncer)
Transaction mode is recommended for scaling to thousands of clients while keeping PostgreSQL connections low (e.g., 20-50).

```ini
[pgbouncer]
pool_mode = transaction
listen_port = 6432
max_client_conn = 2000
default_pool_size = 30
reserve_pool_size = 10
```

**Rule of Thumb:**
Total DB connections should be `(2 * CPU cores) + disk speed factor`. Adding more connections beyond the hardware's ability to process them concurrently decreases throughput due to contention.

## Lock Management

Locking is necessary for consistency but is the primary cause of application latency and deadlocks.

### Common Lock Types and Conflicts

| Lock | Impact | Conflicting Locks |
| :--- | :--- | :--- |
| RowExclusive | INSERT, UPDATE, DELETE | AccessExclusive (e.g., ALTER TABLE) |
| ShareLock | CREATE INDEX | RowExclusive (Blocks writes) |
| AccessExclusive | ALTER TABLE, DROP, TRUNCATE | Everything (Blocks all access) |

### Non-Blocking DDL Strategies
Always use `CONCURRENTLY` for index operations in production to avoid blocking writes.

```sql
-- Blocks writes to the table for the duration of index build
CREATE INDEX idx_user_email ON users(email); 

-- Builds in background, does not block reads or writes
CREATE INDEX CONCURRENTLY idx_user_email ON users(email);
```

For schema changes, use short lock timeouts to prevent a "lock queue" from taking down the site:

```sql
-- Set local timeout so the migration fails quickly instead of blocking
SET lock_timeout = '2s';
ALTER TABLE users ADD COLUMN phone_number TEXT;
```

### Advisory Locks
Advisory locks allow applications to use the database's locking engine for their own needs (e.g., ensuring only one worker processes a specific job).

```sql
-- Acquire a session-level lock
SELECT pg_advisory_lock(54321);

-- Try to acquire; return false immediately if held by another
SELECT pg_try_advisory_lock(54321);

-- Release
SELECT pg_advisory_unlock(54321);
```

### Monitoring Locks and Deadlocks
If queries are hanging, check `pg_stat_activity` and `pg_locks` to find the culprit:

```sql
SELECT 
    blocked_locks.pid     AS blocked_pid,
    blocking_locks.pid    AS blocking_pid,
    blocked_activity.query AS blocked_statement,
    blocking_activity.query AS blocking_statement
FROM  pg_catalog.pg_locks         blocked_locks
JOIN pg_catalog.pg_stat_activity  blocked_activity  ON blocked_locks.pid = blocked_activity.pid
JOIN pg_catalog.pg_locks          blocking_locks 
    ON blocking_locks.locktype = blocked_locks.locktype
    AND blocking_locks.DATABASE IS NOT DISTINCT FROM blocked_locks.DATABASE
    AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
    AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
    AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
    AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
    AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
    AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
    AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
    AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
    AND blocking_locks.pid != blocked_locks.pid
JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_locks.pid = blocking_activity.pid
WHERE NOT blocked_locks.granted;
```

## pg_stat_statements

This extension is mandatory for production databases. It records statistics for every query executed, allowing you to find the "heaviest" queries by time, I/O, or frequency.

### Setup
Add to `postgresql.conf` and restart:
```conf
shared_preload_libraries = 'pg_stat_statements'
pg_stat_statements.track = all
pg_stat_statements.max = 10000
```

### Identifying Performance Bottlenecks

```sql
-- Top 5 queries taking the most total time (The "Wall of Shame")
SELECT query, calls, total_exec_time, mean_exec_time, rows
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 5;

-- Queries producing the most temp files (low work_mem)
SELECT query, temp_blks_read, temp_blks_written
FROM pg_stat_statements
WHERE temp_blks_read > 0
ORDER BY temp_blks_read DESC
LIMIT 5;

-- Find queries with high variance (inconsistent performance)
SELECT query, stddev_exec_time / mean_exec_time as variance_coefficient
FROM pg_stat_statements
WHERE calls > 100
ORDER BY variance_coefficient DESC
LIMIT 5;
```

## Write Ahead Log (WAL) Configuration

The WAL ensures data durability. Tuning it balances crash recovery time against write performance.

| Parameter | Recommended Setting | Reason |
| :--- | :--- | :--- |
| wal_level | `replica` | Minimum for replication/backups. |
| max_wal_size | `4GB` to `16GB` | Prevents frequent checkpoints. |
| min_wal_size | `1GB` | Pre-allocates space for WAL files. |
| checkpoint_timeout | `15min` | Reduces I/O spikes from checkpoints. |
| checkpoint_completion_target | `0.9` | Spreads write load across the timeout. |
| wal_compression | `on` | Reduces WAL volume at cost of slight CPU. |

### WAL Archiving Tuning
For production databases requiring Point-In-Time Recovery (PITR):
```conf
archive_mode = on
archive_command = 'test ! -f /path/to/archive/%f && cp %p /path/to/archive/%f'
archive_timeout = 60s # Force a WAL segment switch every 60s
```

## Parallel Query Tuning

PostgreSQL can use multiple CPU cores to execute a single query. This is vital for analytical workloads.

| Parameter | Recommendation |
| :--- | :--- |
| max_parallel_workers_per_gather | 2 to 4 (depending on core count). |
| max_parallel_workers | Total CPU cores available to PG. |
| parallel_tuple_cost | 0.1 (reduce if PG is too "shy" to parallelize). |
| min_parallel_table_scan_size | 8MB (don't parallelize tiny tables). |

## Configuration Workflow

When setting up or tuning a PostgreSQL instance, follow this sequence:

1. **Calculate Baseline Memory:** Set `shared_buffers` to 25% RAM and `effective_cache_size` to 75% RAM.
2. **Configure Kernel:** Disable THP and set `vm.swappiness=1` and `vm.overcommit_memory=2`.
3. **Optimize for Storage:** Set `random_page_cost` to 1.1 if using SSDs.
4. **Control Query Memory:** Calculate `work_mem` based on `max_connections` to avoid OOM.
5. **Enable Observability:** Add `pg_stat_statements` to `shared_preload_libraries`.
6. **Tune Autovacuum:** Reduce scale factors for large tables to prevent bloat.
7. **Deploy Connection Pooler:** Use PgBouncer in transaction mode if client count > 100.
8. **Optimize WAL:** Increase `max_wal_size` and `checkpoint_timeout` for write-heavy loads.
9. **Monitor Parallelism:** Adjust `max_parallel_workers` if CPU utilization is low during large scans.
10. **Test and Measure:** Use `EXPLAIN ANALYZE` on slow queries to verify plan changes.

Always apply changes in a staging environment that mirrors production data volume before deploying to the primary database. Small changes to `work_mem` or `random_page_cost` can have massive cascading effects on query plans across the entire application.
