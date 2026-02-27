# MySQL Tuning

Sources: Schwartz (High Performance MySQL), MySQL documentation, Percona best practices

Covers: InnoDB configuration, buffer pool, slow query log, optimizer hints, character sets, replication basics, key differences from PostgreSQL.

## InnoDB Architecture

InnoDB is the default and only recommended storage engine for modern MySQL and MariaDB installations. Its performance is heavily tied to its architecture as a clustered-index engine.

### Clustered Index
In InnoDB, table data is stored directly within the primary key's B-tree. This structure has significant implications for performance and storage:
- The Primary Key (PK) IS the table: Data rows are physically ordered on disk according to the PK value.
- Secondary indexes do not point to physical row offsets. Instead, they store the value of the primary key for each row.
- Primary key lookups are "single-hop" (data is reached immediately), whereas secondary index lookups are "double-hop" (find PK in secondary index, then look up data in the clustered index).

### Key Selection Strategy
- Minimize Primary Key width: Because every secondary index contains the PK value, a wide PK (e.g., a long UUID string) bloats every index and increases I/O.
- Use auto-increment INT or BIGINT: These ensure sequential insertion, minimizing B-tree page splits and fragmentation.
- Avoid random PKs: Inserting random values (like UUID v4) into a clustered index forces constant re-ordering of data on disk, leading to high I/O and fragmented pages.

### Page Size and Row Formats
InnoDB manages data in pages (default 16KB). The row format determines how data is physically stored within these pages.
- DYNAMIC (Default): Optimized for rows with large BLOB or VARCHAR columns. Off-page storage is used for large values, keeping the clustered index leaf nodes lean.
- COMPRESSED: Reduces disk I/O and storage space at the cost of increased CPU usage for decompression.
- BARRACUDA: The file format supporting DYNAMIC and COMPRESSED row formats. Ensure `innodb_file_per_table` is enabled to manage tablespaces effectively.

## Memory Configuration

MySQL allocates memory globally and per-connection. Over-allocating per-connection buffers can lead to OOM (Out of Memory) kills if connection counts spike.

| Parameter | Purpose | Recommended Setting |
| :--- | :--- | :--- |
| innodb_buffer_pool_size | Cache for data and indexes | 70-80% of RAM on dedicated servers |
| innodb_buffer_pool_instances | Reduces contention in the pool | 8 (default) or 1 per GB of pool size |
| innodb_buffer_pool_chunk_size | Unit for resizing buffer pool | Default 128MB. instances * chunk_size must <= buffer_pool_size |
| innodb_log_buffer_size | Buffer for redo log transactions | 64MB - 256MB |
| innodb_adaptive_hash_index | Internal hash for frequent lookups | ON (default), but monitor for contention on high-concurrency write loads |
| sort_buffer_size | Memory for ORDER BY/GROUP BY | 256KB - 2MB (Per-connection) |
| join_buffer_size | Buffer for non-indexed joins | 256KB - 1MB (Per-connection) |
| tmp_table_size | Max size for in-memory temp tables | 64MB - 256MB |
| max_heap_table_size | Max size for MEMORY engine tables | Match tmp_table_size |

### Configuration Example
```ini
[mysqld]
# 32GB RAM Server Example
innodb_buffer_pool_size = 24G
innodb_buffer_pool_instances = 24
innodb_log_buffer_size = 128M
sort_buffer_size = 1M
join_buffer_size = 1M
tmp_table_size = 128M
max_heap_table_size = 128M

# Per-thread memory limits
max_connections = 500
thread_stack = 256K
```

## InnoDB Flush Settings

Flushing behavior determines the balance between data safety (ACID compliance) and write performance.

| Parameter | Value | Impact on Performance and Safety |
| :--- | :---: | :--- |
| innodb_flush_log_at_trx_commit | 1 | Full ACID. Log is flushed to disk at every commit. Safest, slowest. |
| innodb_flush_log_at_trx_commit | 2 | Log is written to OS cache at commit, flushed to disk once per second. |
| innodb_flush_log_at_trx_commit | 0 | Log is written and flushed once per second. Fastest, risk 1s data loss. |
| innodb_flush_method | O_DIRECT | Direct I/O to disk, bypassing OS page cache. Prevents double buffering. |
| innodb_io_capacity | 2000 | Background I/O rate. Set to 200 for HDD, 2000-10000+ for SSD. |
| innodb_io_capacity_max | 4000 | Maximum burst I/O capacity. Usually 2x innodb_io_capacity. |

### Decision Logic
- Use 1: Financial transactions, critical user data, or systems where data loss is unacceptable.
- Use 2: Most web applications. Data is safe unless the Operating System crashes or power fails.
- Use 0: Only for non-critical data, logs, or temporary processing tables.

## Slow Query Log

The slow query log is the primary diagnostic tool for identifying performance bottlenecks.

### Activation and Configuration
```ini
[mysqld]
slow_query_log = ON
slow_query_log_file = /var/log/mysql/slow.log
long_query_time = 0.1             # Log queries taking longer than 100ms
log_queries_not_using_indexes = ON # Log queries that scan entire tables
min_examined_row_limit = 100      # Avoid logging trivial small table scans
log_slow_admin_statements = ON    # Include OPTIMIZE/ALTER in log
```

### Analysis Tools
Raw logs are difficult to read. Use aggregation tools to find the most impactful queries.
1. mysqldumpslow: Basic tool bundled with MySQL.
2. pt-query-digest: Advanced tool from Percona Toolkit. It ranks queries by total execution time (Load).

```bash
# Analyze the top 10 most expensive queries by load
pt-query-digest /var/log/mysql/slow.log --limit 10

# Filter by specific database
pt-query-digest /var/log/mysql/slow.log --filter '$event->{db} eq "production"'
```

### Log Rotation
To prevent the slow log from consuming all disk space, implement rotation via `logrotate` or MySQL's internal global variables.
```bash
# Manual rotation
mv /var/log/mysql/slow.log /var/log/mysql/slow.log.old
mysqladmin flush-logs
```

## Optimizer Hints (MySQL 8.0+)

Optimizer hints allow manual override of the MySQL execution plan when the optimizer chooses a sub-optimal path.

### Index and Join Hints
```sql
-- Force the use of a specific index
SELECT /*+ INDEX(orders idx_customer_id) */ * 
FROM orders 
WHERE customer_id = 123;

-- Specify join order to prevent expensive nested loops
SELECT /*+ JOIN_ORDER(orders, customers) */ * 
FROM orders 
JOIN customers ON orders.customer_id = customers.id;
```

### Execution Strategy Hints
```sql
-- Increase sort memory for a specific large query
SELECT /*+ SET_VAR(sort_buffer_size = 16M) */ * 
FROM large_table 
ORDER BY created_at;

-- Disable index merge if it causes performance regression
SELECT /*+ NO_INDEX_MERGE(users) */ * 
FROM users 
WHERE email = 'a@b.com' OR phone = '123';

-- Force a hash join (useful for large non-indexed joins)
SELECT /*+ HASH_JOIN(t1, t2) */ * 
FROM t1 
JOIN t2 ON t1.val = t2.val;

-- Block Nested Loop (BNL) control
SELECT /*+ NO_BNL(t1, t2) */ * FROM t1, t2;

-- Index Condition Pushdown (ICP) control
SELECT /*+ NO_ICP(orders) */ * FROM orders WHERE city = 'NYC' AND age > 25;
```

## Character Sets

MySQL's character set history is a common source of bugs and performance issues.

### utf8 vs utf8mb4
- Never use `utf8`: In MySQL, `utf8` is an alias for `utf8mb3`, which only supports 3-byte characters. This excludes emojis and many mathematical symbols.
- Always use `utf8mb4`: This is the true 4-byte UTF-8 implementation.

### Collation
Collation determines how strings are compared and sorted.
- Default in 8.0: `utf8mb4_0900_ai_ci`
- `ai`: Accent-insensitive (e = é)
- `ci`: Case-insensitive (a = A)

```sql
-- Database-level configuration
CREATE DATABASE production_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;

-- Table-level column override
CREATE TABLE comments (
  id BIGINT PRIMARY KEY,
  content TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin -- Binary for case-sensitive
);
```

## MySQL vs PostgreSQL Key Differences

Understanding the architectural differences is critical for developers moving between systems.

| Feature | PostgreSQL | MySQL (InnoDB) |
| :--- | :--- | :--- |
| Clustered Index | Optional (via CLUSTER, not maintained) | Mandatory (PK is the clustered index) |
| MVCC Storage | Heap + Dead Tuples (requires VACUUM) | Undo Log + Purge Thread (automatic) |
| NULLs in UNIQUE | Multiple NULLs allowed | Multiple NULLs allowed |
| Foreign Key Indexes | Manual creation required | Automatically created by MySQL |
| Partial Indexes | Supported (`WHERE status = 'active'`) | Not supported |
| Expression Indexes | Supported natively | Generated Columns + Index |
| Execution Analysis | `EXPLAIN ANALYZE` (Long standing) | `EXPLAIN ANALYZE` (Available in 8.0.18+) |
| CTE Support | Optimized/Inlined (PG 12+) | Materialized (Historically, 8.0.35+ improved) |
| Window Functions | Comprehensive support since 8.4 | Introduced in 8.0 |
| JSON Support | JSONB (Binary, GIN indexing) | JSON (Binary, Generated Column indexing) |
| Upsert Syntax | `ON CONFLICT DO UPDATE` | `ON DUPLICATE KEY UPDATE` |
| Returning Data | `INSERT ... RETURNING id` | Use `LAST_INSERT_ID()` after execute |
| Parallel Query | Strong support for CPU parallelism | Very limited parallelism |
| Connection Model | Process-per-connection | Thread-per-connection |
| Full Text Search | TSVector / GIN Indexes | FullText Indexes (B-tree based) |
| Triggers | per-statement or per-row | per-row only |
| Sequences | First-class objects | AUTO_INCREMENT column attribute |
| Default Isolation | Read Committed | Repeatable Read |

## Replication Basics

MySQL replication is typically used for read scaling, high availability, and backups.

### Replication Modes
1. Asynchronous: Primary commits locally, then sends logs to replicas. Low latency, risk of data lag.
2. Semi-Synchronous: Primary waits for at least one replica to acknowledge receipt of logs before confirming commit. Better durability.
3. Group Replication: Multi-primary or single-primary clusters with built-in conflict detection and consensus.

### Binary Log Formats
- ROW (Recommended): Records the actual changes to rows. Most reliable, prevents non-deterministic function bugs.
- STATEMENT: Records the SQL statements. Uses less space but can lead to data drift if queries are non-deterministic (e.g., `LIMIT` without `ORDER BY`).
- MIXED: Automatically switches between statement and row based on query complexity.

### Scaling Reads
To scale read operations, replicas should be configured to prevent accidental writes.
```ini
[mysqld]
# Configuration for Read Replicas
read_only = ON
super_read_only = ON # Prevents even 'super' users from writing
log_slave_updates = ON # Required if daisy-chaining replicas
```
Applications must implement logic to send `SELECT` queries to replicas and `INSERT/UPDATE/DELETE` to the primary.

## InnoDB Online DDL

MySQL 8.0 supports "Instant" and "Online" DDL for many common operations, reducing or eliminating table locking.

| Operation | Strategy | Concurrent DML Allowed? |
| :--- | :--- | :--- |
| ADD COLUMN (at end) | Instant | Yes |
| DROP COLUMN | Rebuild | Yes |
| MODIFY COLUMN TYPE | Rebuild | Yes |
| RENAME COLUMN | Instant | Yes |
| ADD INDEX | In-place | Yes |
| DROP INDEX | In-place | Yes |
| ADD FOREIGN KEY | In-place | Yes |
| SET DEFAULT | Instant | Yes |

### Metadata Locks
Even "Instant" DDL requires a brief metadata lock at the start and end of the operation. If there is a long-running transaction (e.g., a multi-hour report query) on the table, the DDL operation will wait, and subsequent queries will queue behind the DDL, effectively blocking the table. Always check `SHOW PROCESSLIST` before running DDL on busy tables.

### Large Table Alterations
For tables exceeding 100GB, native Online DDL can still cause metadata lock contention or excessive temporary space usage. In these cases, use external tools:
- pt-online-schema-change: Uses triggers to sync data to a new table.
- gh-ost: Uses the binary log to sync data (no triggers), reducing load on the primary.

## Anti-Patterns Specific to MySQL

Avoid these common mistakes to maintain performance and stability.

1. **Using MyISAM Storage Engine**: MyISAM lacks transactions, uses table-level locking, and is prone to corruption on crashes. Always use InnoDB.
2. **Using utf8 instead of utf8mb4**: This will cause "Incorrect string value" errors when users input emojis or special characters.
3. **Too Many Connections**: Each connection consumes memory for buffers (sort, join). Set `max_connections` reasonably (e.g., 500-1000) and use application-side connection pooling.
4. **Wide Primary Keys**: Using long strings or multiple columns as a primary key increases the size of every secondary index and decreases buffer pool efficiency.
5. **Relying on Query Cache**: The query cache was removed in MySQL 8.0 because it caused massive global mutex contention. Use ProxySQL or an application-level cache (Redis/Memcached) instead.
6. **SELECT * in Application Code**: Always specify columns. This reduces network I/O and increases the chance of "Covering Index" optimizations.
7. **Implicit Type Conversion**: Comparing a string column to a numeric value (`WHERE string_col = 123`) prevents index usage. Ensure data types match in queries.
8. **Over-Indexing**: Every index adds overhead to writes. Periodically check for unused indexes using `sys.schema_unused_indexes`.
9. **Ignoring AUTO_INCREMENT exhaustion**: Using `INT` for a high-traffic table's PK can lead to exhaustion at 2.1 billion. Always use `BIGINT` for large datasets.
10. **Using Large BLOBs/TEXT in Clustered Index**: Large objects stored in-row increase the height of the B-tree. Use `DYNAMIC` row format to push them off-page.
