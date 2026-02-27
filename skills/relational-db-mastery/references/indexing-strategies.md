# Indexing Strategies

Sources: Winand (SQL Performance Explained), Petrov (Database Internals), PostgreSQL/MySQL documentation

Covers: index types, selection framework, composite indexes, specialized indexes, anti-patterns.

## B-Tree Indexes (Default)

The B-tree (Balanced Tree) is the workhorse of relational databases. It maintains data in a sorted structure, allowing for efficient searches, insertions, and deletions.

### Mechanics
- **Structure**: A multi-level tree of pages (blocks). Leaves contain either the actual row data (clustered) or pointers to the heap (non-clustered).
- **Nodes**: Internal nodes store keys and child pointers to direct the search. Leaf nodes store keys and data/pointers, and are linked to each other for sequential range scans.
- **Balancing**: B-trees remain balanced through page splits and merges. A search from root to leaf always takes the same number of steps, regardless of where the data is in the tree.
- **Complexity**: Search, insert, and delete operations take O(log n) time.
- **Sorting**: Data is stored in a logical sort order. This is why B-trees support range queries and ORDER BY optimization.

### Best For
- **Equality**: `WHERE column = 'value'`
- **Range**: `WHERE column > 10 AND column < 100`
- **Prefix Matching**: `WHERE name LIKE 'Ant%'` (only if the pattern does not start with a wildcard)
- **Sorting**: `ORDER BY column`
- **Aggregates**: `MIN(column)`, `MAX(column)`

```sql
-- Standard B-tree index in PostgreSQL
CREATE INDEX idx_users_email ON users(email);

-- Unique index enforces integrity and creates B-tree
CREATE UNIQUE INDEX idx_users_username ON users(username);
```

## Index Design Workflow

When designing indexes for a new feature, follow this systematic process:

1. **Query Audit**: Identify the most frequent and most expensive queries. Focus on `WHERE`, `JOIN`, and `ORDER BY` clauses.
2. **Cardinality Analysis**: Check the number of unique values in potential index columns. Low cardinality columns (e.g., `gender`, `is_active`) are poor candidates for B-trees unless used in composite or partial indexes.
3. **Application of E-R-S**: For multi-filter queries, apply the Equality-Range-Sort rule to order columns in a composite index.
4. **Constraint Verification**: Identify unique requirements. Unique indexes serve as both performance tools and data integrity guards.
5. **Space-Performance Trade-off**: Evaluate if a covering index (`INCLUDE`) is worth the disk space and write overhead for a specific high-frequency query.
6. **Implementation with CONCURRENTLY**: Always deploy indexes using non-blocking methods in production environments.
7. **Verification**: Use `EXPLAIN ANALYZE` (covered in separate reference) to confirm the optimizer actually selects the new index.

## Index Type Selection Decision Tree

Use this framework to select the appropriate index type based on query patterns.

| Query Pattern | Best Index Type | Why | Example |
| :--- | :--- | :--- | :--- |
| Equality (=, IN) | B-tree | Default, highly optimized for exact matches | `WHERE status = 'active'` |
| Range (<, >, BETWEEN) | B-tree | Sorted structure enables efficient range scans | `WHERE price > 500` |
| Text Search (Complex) | GIN | Inverted index for lexemes and full-text vectors | `WHERE text @@ to_tsquery('sql')` |
| Array Operations | GIN | Efficient for "contains" (@>) and "overlaps" (&&) | `WHERE tags @> '{db}'` |
| JSONB Queries | GIN | Indexes keys and values for containment | `WHERE doc @> '{"id": 1}'` |
| Geometric / Range | GiST | Supports overlapping, containment, and R-tree | `WHERE loc && '((0,0),(1,1))'` |
| Nearest Neighbor | GiST | Specialized index for KNN (distance) searches | `ORDER BY loc <-> point(0,0)` |
| Massive Append-only | BRIN | Block-range summary; tiny footprint for sorted logs | `WHERE log_time > now() - interval '1h'` |
| Equality (Strict) | Hash | Slightly faster for =; no range support | `WHERE uuid = '...'` (PG 10+) |

## Composite (Multi-Column) Indexes

A composite index is an index on multiple columns. The order of columns is critical for query performance.

### Leftmost Prefix Rule
A B-tree index on `(a, b, c)` can satisfy queries on:
- `(a)`
- `(a, b)`
- `(a, b, c)`

It **cannot** (efficiently) satisfy queries on:
- `(b)`
- `(c)`
- `(b, c)`

### The E-R-S Rule for Column Order
To determine the optimal column order for a query, follow the **Equality → Range → Sort** (E-R-S) hierarchy:

1. **Equality Columns**: Place columns filtered with `=` or `IN` first. These minimize the initial search space.
2. **Range Columns**: Place columns filtered with `<`, `>`, or `BETWEEN` after equality columns.
3. **Sort Columns**: Place columns used in `ORDER BY` last if they follow the filtered columns' sort order.

**Example Query**:
```sql
SELECT * FROM orders
WHERE customer_id = 50       -- Equality
  AND status = 'shipped'     -- Equality
  AND order_date > '2024-01-01' -- Range
ORDER BY amount DESC;         -- Sort
```
**Optimal Index**:
`CREATE INDEX idx_orders_composite ON orders(customer_id, status, order_date, amount);`

### Column Order Impact Matrix
| Query WHERE clause | Index (a, b) | Index (b, a) |
| :--- | :--- | :--- |
| `WHERE a = 1 AND b = 1` | Efficient | Efficient |
| `WHERE a = 1 AND b > 1` | Efficient | Partial Scan (Inefficient) |
| `WHERE a > 1 AND b = 1` | Partial Scan (Inefficient) | Efficient |
| `WHERE a = 1 ORDER BY b` | Efficient (Sorted) | Inefficient (Sort needed) |

## Covering Indexes (INCLUDE)

A covering index is an index that contains all columns requested by a query, allowing the database to skip reading the table (heap) entirely. This is called an **Index-Only Scan**.

### PostgreSQL INCLUDE Clause
PostgreSQL allows attaching non-key columns to an index using the `INCLUDE` clause. These columns are stored only at the leaf nodes and are not used for searching.

```sql
-- Index for: SELECT total, status FROM orders WHERE customer_id = 5
CREATE INDEX idx_orders_cust_id_covering 
ON orders(customer_id) 
INCLUDE (total, status);
```

### Constraints and Costs
- **Visibility Map**: PostgreSQL requires the visibility map to be up to date (via VACUUM) for index-only scans.
- **Write Overhead**: Every update to the `INCLUDE` columns requires updating the index.
- **Size**: Large columns in `INCLUDE` bloat the index, reducing cache efficiency.

## Partial Indexes

A partial index covers only a subset of the rows in a table, defined by a `WHERE` clause in the index definition.

### Use Cases
- **Skewed Data**: When 99% of rows are "processed" and 1% are "pending", index only the "pending" rows.
- **Functional Requirements**: Uniqueness on a column only for active records.

```sql
-- Index only active users for fast login
CREATE INDEX idx_active_users_email 
ON users(email) 
WHERE active IS TRUE;

-- Unique constraint only for non-deleted records
CREATE UNIQUE INDEX idx_unique_name_not_deleted 
ON items(name) 
WHERE deleted_at IS NULL;
```

### Benefits
- **Reduced Size**: Significantly smaller than a full index.
- **Faster Maintenance**: Less overhead during bulk updates to non-matching rows.

## Expression Indexes

Expression indexes (functional indexes) are created on the result of a function or expression rather than on column values directly.

### Usage
The query must use the **exact** expression used in the index definition for the optimizer to recognize it.

```sql
-- Index for case-insensitive search
CREATE INDEX idx_users_lower_email ON users(lower(email));

-- Query that uses the index
SELECT * FROM users WHERE lower(email) = 'test@example.com';

-- Index for JSONB field extraction
CREATE INDEX idx_events_type ON events((data->>'type'));
```

## GIN Indexes Deep Dive

Generalized Inverted Indexes (GIN) are designed for multi-valued data types.

### Primary Use Cases
1. **Full-Text Search**: Inverts words (lexemes) to document IDs.
2. **JSONB**: Indexes the structure of JSON documents.
3. **Arrays**: Maps array elements to row IDs.

```sql
-- Full-text search index
CREATE INDEX idx_articles_fts ON articles USING gin(to_tsvector('english', content));

-- JSONB indexing with jsonb_path_ops (smaller, faster, but supports fewer operators)
CREATE INDEX idx_metadata_path ON logs USING gin(metadata jsonb_path_ops);
```

### Performance Tuning
- **Slower Writes**: GIN indexes are expensive to update.
- **Fast Update**: GIN uses a pending list for updates. Tune `gin_pending_list_limit` for write-heavy workloads.
- **Search Latency**: GIN is extremely fast for searching but can produce large results that require bitmap heap scans.

## GiST Indexes

Generalized Search Trees (GiST) allow the implementation of custom indexing strategies, primarily for geometric and range data.

### Capabilities
- **R-Trees**: Spatial queries (points, polygons, lines).
- **Interval Trees**: Range queries (date ranges, numeric ranges).
- **KNN**: Nearest neighbor search using the distance operator (`<->`).

```sql
-- PostGIS spatial index
CREATE INDEX idx_locations_geom ON locations USING gist(geom);

-- Reservation range overlap prevention
CREATE INDEX idx_reservations_range ON reservations USING gist(during);

-- Query using KNN
SELECT * FROM locations 
ORDER BY geom <-> ST_SetSRID(ST_Point(-74.0, 40.7), 4321) 
LIMIT 5;
```

## BRIN Indexes

Block Range INdexes (BRIN) store summary information (min/max) for ranges of blocks (pages).

### Characteristics
- **Size**: Extremely small (e.g., 30KB for a 10GB table).
- **Workload**: Optimized for very large tables where data is physically correlated with the indexed column (e.g., time-series).
- **Mechanism**: The engine checks the min/max of a range; if the requested value is outside, the entire block range is skipped.

```sql
-- BRIN index on a large log table
CREATE INDEX idx_logs_brin_time 
ON big_logs USING brin(created_at) 
WITH (pages_per_range = 32);
```

### Limitations
- **Precision**: Does not provide point lookup speed.
- **Updates**: Data fragmentation (out-of-order inserts) degrades BRIN performance.

## Indexing Anti-Patterns

Avoid these common mistakes to maintain database health.

| Anti-Pattern | Problem | Fix |
| :--- | :--- | :--- |
| Over-indexing | High write latency, disk bloat, optimizer confusion. | Audit usage; remove indexes with 0 or low `idx_scan`. |
| Unindexed Foreign Keys | Slow JOINs and lock contention during CASCADE deletes. | Always index FK columns unless the table is tiny. |
| Low Cardinality | B-tree on a boolean or status column with few values. | Use a Partial Index for the rare value or skip. |
| Redundant Indexes | Index `(a)` is redundant if `(a, b)` exists. | Drop the narrower index. |
| Every Column Index | Massive write penalty for every INSERT/UPDATE. | Index for specific Query Patterns, not individual columns. |
| Improper Prefix | Querying `WHERE b = 1` using index `(a, b)`. | Reorder columns to `(b, a)` or create a second index. |
| Function Mismatch | `WHERE date(ts) = ...` doesn't use index on `ts`. | Create an expression index or fix the query. |
| Unused GIN | GIN on JSONB when only 2 fields are ever queried. | Use B-tree expression indexes for those specific fields. |

## Index Maintenance

Indexes are not "set and forget". They require monitoring and maintenance.

### Concurrency
Creating an index locks the table for writes by default. Use `CONCURRENTLY` in production.

```sql
-- PostgreSQL: Non-blocking index creation
CREATE INDEX CONCURRENTLY idx_users_email ON users(email);

-- MySQL 8.0+: Online DDL (default behavior for many operations)
ALTER TABLE users ADD INDEX (email), ALGORITHM=INPLACE, LOCK=NONE;
```

### Monitoring Usage (PostgreSQL)
Query `pg_stat_user_indexes` to find unused indexes.

```sql
SELECT 
    relname AS table_name, 
    indexrelname AS index_name, 
    idx_scan,             -- Number of scans started
    idx_tup_read,         -- Tuples read from index
    idx_tup_fetch         -- Tuples fetched from heap
FROM pg_stat_user_indexes
WHERE idx_scan = 0 
  AND schemaname = 'public';
```

### Bloat and Fragmentation
High DELETE/UPDATE activity causes index bloat.
- **PostgreSQL**: Use `REINDEX INDEX CONCURRENTLY` to rebuild without blocking.
- **MySQL**: Use `OPTIMIZE TABLE` to reorganize InnoDB tables and indexes.

## Index Cardinality and Statistics

The database optimizer uses statistics to decide whether to use an index. If an index is not "selective" enough, the optimizer will prefer a Sequential Scan.

### Understanding Selectivity
- **Cardinality**: The number of unique values in a column.
- **Selectivity Ratio**: `(Number of unique values) / (Total number of rows)`.
- **Threshold**: Generally, if a query is expected to return more than 5-10% of the table rows, the overhead of random I/O from a non-clustered index makes a sequential scan faster.

### Statistics Collection
- **PostgreSQL**: The `ANALYZE` command (or the `autovacuum` daemon) updates `pg_stats`.
- **MySQL**: The `ANALYZE TABLE` command updates index cardinality estimates in `information_schema`.

```sql
-- View statistics for a specific column in PostgreSQL
SELECT 
    null_frac, 
    n_distinct, 
    most_common_vals, 
    most_common_freqs 
FROM pg_stats 
WHERE tablename = 'users' AND attname = 'status';
```

## Deep Dive: JSONB Indexing Strategies

PostgreSQL offers multiple ways to index JSONB, each with different trade-offs.

### 1. GIN with Default Opclass (`jsonb_ops`)
- **Supports**: `@>`, `?`, `?&`, `?|` operators.
- **Mechanism**: Indexes every key and value in the JSON tree.
- **Trade-off**: Flexible but produces large indexes.

### 2. GIN with Path Opclass (`jsonb_path_ops`)
- **Supports**: Only the containment operator `@>`.
- **Mechanism**: Creates hashes of entire paths (e.g., `key.subkey.value`).
- **Trade-off**: Smaller and faster than default, but less flexible.

### 3. Expression Index on Specific Field
- **Use Case**: When you only ever query one or two specific keys.
- **Mechanism**: Extracts the value and stores it in a standard B-tree.
- **Trade-off**: Minimal overhead, very fast for equality/range on those fields.

```sql
-- Option 1: Default GIN (Flexible)
CREATE INDEX idx_json_full ON events USING gin(data);

-- Option 2: Path GIN (Performant for containment)
CREATE INDEX idx_json_path ON events USING gin(data jsonb_path_ops);

-- Option 3: B-tree on specific field (Fastest for specific lookups)
CREATE INDEX idx_json_user_id ON events((data->>'user_id'));
```

## Advanced Maintenance and Monitoring

Beyond simple usage counts, deep maintenance requires understanding bloat and fragmentation.

### Identifying Index Bloat (PostgreSQL)
Index bloat occurs when space is allocated to an index but not used by active rows, often due to massive updates/deletes and insufficient vacuuming.

```sql
-- Approximate bloat calculation (requires pgstattuple extension)
SELECT * FROM pgstatindex('idx_users_email');
-- Look for 'avg_leaf_density'. Values < 50-60% indicate significant bloat.
```

### Finding Duplicate and Redundant Indexes
Duplicate indexes waste storage and slow down writes without providing any benefit.

```sql
-- Find indexes that are prefixes of other indexes
SELECT
    ind1.relname AS redundant_index,
    ind2.relname AS primary_index
FROM pg_index i1
JOIN pg_class ind1 ON ind1.oid = i1.indexrelid
JOIN pg_index i2 ON i1.indrelid = i2.indrelid AND i1.indexrelid != i2.indexrelid
JOIN pg_class ind2 ON ind2.oid = i2.indexrelid
WHERE i2.indkey[0:array_upper(i1.indkey,1)-1] = i1.indkey
  AND i1.indisunique IS FALSE;
```

### MySQL: Monitoring Index Efficiency
Use the Performance Schema to track index usage and latency.

```sql
-- Find unused indexes in MySQL
SELECT * FROM sys.schema_unused_indexes;

-- Index statistics with latency
SELECT * FROM sys.schema_index_statistics 
WHERE table_name = 'orders' 
ORDER BY select_latency DESC;
```

## PostgreSQL vs MySQL Index Differences

While both support B-trees, their implementation and specialized index support differ significantly.

| Feature | PostgreSQL | MySQL (InnoDB) |
| :--- | :--- | :--- |
| **B-tree** | Default; non-clustered. | Clustered (PK stores data; secondary indexes store PK). |
| **GIN** | Native (FTS, JSONB, Arrays). | Limited (Full-text only). |
| **GiST / BRIN** | Native; highly extensible. | Not supported. |
| **Partial Index** | Native `WHERE` clause support. | Not supported (use generated columns workaround). |
| **Expression Index** | Native support. | Generated Columns (MySQL 5.7) or Functional (MySQL 8.0). |
| **Covering (INCLUDE)**| Native `INCLUDE` clause. | Secondary indexes are naturally covering for PK. |
| **Hash Index** | WAL-logged and crash-safe (PG 10+). | Only for MEMORY engine; InnoDB has Adaptive Hash. |
| **Spatial** | GiST / PostGIS (Industry Lead). | SPATIAL index (B-tree based R-tree). |
| **Creation** | `CREATE INDEX CONCURRENTLY`. | `ALGORITHM=INPLACE, LOCK=NONE`. |
| **Invisible Indexes** | Not native (use `pg_index` hacking). | Native support (MySQL 8.0) for testing before drop. |

### MySQL Specific: Clustered Index Impact
In MySQL InnoDB, the Primary Key is the clustered index. Secondary indexes store the Primary Key value as the pointer. 
- **Guideline**: Keep Primary Keys small (e.g., INT/BIGINT) to minimize secondary index size.
- **Covering Logic**: Every secondary index automatically "covers" the Primary Key column.

### PostgreSQL Specific: Visibility Map
An Index-Only Scan in PostgreSQL requires the visibility map to confirm a page contains only visible tuples.
- **Guideline**: Frequent updates to a table reduce the effectiveness of covering indexes unless VACUUM is aggressive.
