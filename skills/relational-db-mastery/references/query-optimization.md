# Query Optimization Patterns

Sources: Winand (SQL Performance Explained), Karwin (SQL Antipatterns), PostgreSQL/MySQL documentation
Covers: JOIN optimization, subquery vs CTE, pagination, batch operations, N+1, window functions, query rewriting.

## JOIN Optimization

Efficiency in JOIN operations is the cornerstone of relational database performance. While modern optimizers are sophisticated, understanding the underlying mechanics allows for writing queries that the optimizer can effectively handle.

### JOIN Mechanics and Order

In theory, the JOIN order of tables determines the size of intermediate results. The goal is to reduce the result set as early as possible.

- **Smaller result set first**: Ideally, start with the table that has the most restrictive filter (WHERE clause). This minimizes the work for subsequent JOINs.
- **INNER vs LEFT JOIN**: INNER JOINs are generally more performant because they give the optimizer more freedom to reorder tables. LEFT JOINs impose a semantic order that the optimizer must respect unless it can prove an INNER JOIN would yield the same result.
- **Index usage**: Ensure that all JOIN conditions are on indexed columns. For `A JOIN B ON A.x = B.y`, both `A.x` and `B.y` should be indexed, or at least the "inner" side of the specific join strategy used.

### Sargability in JOINs

Avoid using functions on columns within JOIN conditions. This "kills" the ability to use standard B-tree indexes.

```sql
-- Bad: Non-sargable JOIN condition
SELECT * FROM users u 
JOIN orders o ON lower(u.email) = lower(o.contact_email);

-- Good: Sargable condition or use of functional indexes (PostgreSQL)
SELECT * FROM users u 
JOIN orders o ON u.email = o.contact_email;
```

### Join Strategies Comparison

The database engine chooses a join strategy based on table statistics, indexes, and memory availability.

| Join Type | Mechanism | Memory Usage | Sorted Input Required? |
| :--- | :--- | :--- | :--- |
| **Nested Loop** | Iterates through outer table, looks up each row in inner table. | Very Low | No |
| **Hash Join** | Loads smaller table into a hash map, then scans larger table. | High | No |
| **Merge Join** | Walks through both tables in order (like a merge sort step). | Low | Yes (Both sides) |

- **Nested Loop Performance**: Most efficient for small result sets where the inner table has a highly selective index (e.g., primary key). If the inner table is large and not indexed, this becomes O(n*m).
- **Hash Join Performance**: Best for large, unsorted datasets where memory is available. It is particularly effective for equality joins (`=`). If the hash table exceeds `work_mem` (PostgreSQL), it must "spill to disk," causing significant slowdowns.
- **Merge Join Performance**: Best when both tables are already sorted by the join key (e.g., via an index scan). It is the preferred method for inequality joins (`>`, `<`) on large datasets where a Hash Join cannot be used.

## Subquery vs JOIN vs CTE

Choosing the right structure for complex queries impacts both readability and execution plans.

| Pattern | Performance | Readability | When to Use |
| :--- | :--- | :--- | :--- |
| **Subquery (WHERE)** | Variable; can be slow if correlated | Low | EXISTS checks, simple membership tests |
| **Subquery (FROM)** | Usually materialized once | Medium | Aggregating a subset before joining |
| **JOIN** | Usually fastest; highly optimized | Medium | Direct one-to-one or one-to-many relations |
| **CTE (Common Table Expression)** | Materialized in PG <12; flexible in PG 12+ | High | Multi-step logic, recursive queries |
| **LATERAL JOIN** | Row-by-row correlation | Medium | Top-N per group, functions returning sets |

### CTE Optimization in PostgreSQL

PostgreSQL 12 introduced changes to how CTEs are handled. By default, non-recursive CTEs are inlined if they are used only once and are not side-effecting.

```sql
-- Explicitly control materialization in PG 12+
WITH regional_sales AS NOT MATERIALIZED (
    SELECT region, SUM(amount) AS total_sales
    FROM orders
    GROUP BY region
)
SELECT * FROM regional_sales WHERE total_sales > 10000;
```

In MySQL 8.0+, CTEs are supported but are generally materialized, which can lead to overhead if the CTE result set is large.

## N+1 Query Problem

The N+1 problem occurs when an application executes one query to fetch parent records and then executes N additional queries (one for each parent) to fetch related child records.

### Detection

If your database logs show a high volume of near-identical queries with different parameters, you likely have an N+1 issue.

```sql
-- Log output for N+1
SELECT * FROM posts LIMIT 10;
SELECT * FROM comments WHERE post_id = 1;
SELECT * FROM comments WHERE post_id = 2;
-- ... repeat 8 more times
```

### Fixes

1. **JOINing and Application Mapping**:
   Fetch everything in one query and group in the application.
   ```sql
   SELECT p.*, c.* FROM posts p 
   LEFT JOIN comments c ON p.id = c.post_id 
   WHERE p.id IN (1, 2, 3...);
   ```

2. **Batch Loading**:
   Collect IDs first, then fetch children in one bulk query.
   ```sql
   SELECT * FROM comments WHERE post_id IN (1, 2, 3, 4, 5...);
   ```

3. **ORM Eager Loading**:
   Most ORMs provide built-in solutions (e.g., Prisma's `include` or SQLAlchemy's `joinedload`).

## Pagination Strategies

Traditional pagination using `OFFSET` and `LIMIT` becomes increasingly slow as the offset grows.

| Strategy | Performance | User Experience | Use Case |
| :--- | :--- | :--- | :--- |
| **OFFSET/LIMIT** | O(offset); slow for deep pages | Page numbers (1, 2, 3...) | Admin panels, small datasets |
| **Keyset (Cursor)** | O(1) consistent performance | Infinite scroll, Next/Prev | APIs, high-volume feeds |
| **Deferred JOIN** | Better than pure OFFSET | Page numbers | Medium sets with wide columns |

### Keyset Pagination Implementation

Keyset pagination uses the value of the last row from the previous page to find the next set.

```sql
-- Initial query
SELECT id, title, created_at FROM posts 
ORDER BY created_at DESC, id DESC LIMIT 20;

-- Subsequent query (using values from the 20th row of previous page)
SELECT id, title, created_at FROM posts 
WHERE (created_at, id) < ('2024-02-27 10:00:00', 54321)
ORDER BY created_at DESC, id DESC LIMIT 20;
```

### Deferred JOIN Pattern

For `OFFSET` pagination on tables with large rows, fetch only the primary keys first, then JOIN back to get the full data. This reduces the amount of data moved through the "discard" phase.

```sql
SELECT p.* FROM posts p
JOIN (
    SELECT id FROM posts
    ORDER BY created_at DESC
    LIMIT 20 OFFSET 10000
) AS sub ON p.id = sub.id;
```

## Batch Operations and Concurrency

Individual DML statements have overhead. Batching amortizes these costs and reduces locking duration.

### Bulk INSERTs and Upserts

```sql
-- Good: Multi-row VALUES list
INSERT INTO logs (message) VALUES ('log1'), ('log2'), ... ('log1000');

-- Best for PostgreSQL: COPY command
COPY logs (message) FROM STDIN;

-- PostgreSQL Batch Upsert
INSERT INTO inventory (sku, quantity)
VALUES ('A1', 10), ('B2', 20)
ON CONFLICT (sku) 
DO UPDATE SET quantity = inventory.quantity + EXCLUDED.quantity;

-- MySQL equivalent
INSERT INTO inventory (sku, quantity)
VALUES ('A1', 10), ('B2', 20)
ON DUPLICATE KEY UPDATE quantity = quantity + VALUES(quantity);
```

### Batch UPDATEs and DELETEs

In PostgreSQL, updating from a `VALUES` list is efficient for batch updates with different values.

```sql
UPDATE products AS p SET
    price = v.price, stock = v.stock
FROM (VALUES (1, 19.99, 100), (2, 25.50, 50)) AS v(id, price, stock)
WHERE p.id = v.id;

-- Chunked Delete pattern to avoid log bloat and long locks
DELETE FROM logs WHERE id IN (
    SELECT id FROM logs WHERE created_at < '2023-01-01' LIMIT 5000
);
```

## Window Functions Optimization

Window functions (`OVER()`) allow for complex analysis without reducing row count.

- **Partitioning**: Always use indexed columns in `PARTITION BY`.
- **Ordering**: The `ORDER BY` inside the window should match an index to avoid a sort step.
- **Filter Early**: Add a `WHERE` clause before applying window functions.

### ROW_NUMBER() for Top-N-Per-Group

```sql
SELECT * FROM (
    SELECT id, customer_id, amount,
        ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY created_at DESC) as rn
    FROM orders WHERE status = 'completed'
) sub WHERE rn = 1;
```

## Recursive CTE Performance

Recursive CTEs are powerful for tree traversal but can easily lead to massive memory usage if not constrained.

```sql
-- Optimized Recursive CTE for Category Hierarchy
WITH RECURSIVE category_path AS (
    SELECT id, name, parent_id, name::text as path
    FROM categories WHERE parent_id IS NULL
  UNION ALL
    SELECT c.id, c.name, c.parent_id, cp.path || ' > ' || c.name
    FROM categories c
    JOIN category_path cp ON c.parent_id = cp.id
    WHERE length(cp.path) < 1000 -- Safety depth limit
)
SELECT * FROM category_path;
```
- **Optimization**: Ensure `parent_id` is indexed. Use `UNION ALL` instead of `UNION` to avoid expensive deduplication.

## Optimizer Hints and Controls

Sometimes you must override or guide the optimizer's choice.

### PostgreSQL (Session Level)

PostgreSQL uses session variables to influence the planner.

```sql
-- Disable hash joins to force nested loop or merge join
SET enable_hashjoin = off;

-- Influence the "cost" of random page access
SET random_page_cost = 1.1;
```

### MySQL (Query Level)

MySQL supports inline hints for indexes and join order.

```sql
-- Force the use of a specific index
SELECT * FROM orders FORCE INDEX (idx_status) WHERE status = 'shipped';

-- Specify the join order
SELECT /*+ JOIN_ORDER(u, o) */ * FROM users u JOIN orders o ON u.id = o.user_id;
```

## Query Rewriting Techniques

Standard patterns that can often be rewritten for better performance.

### Existential Checks and Covered Indexes

```sql
-- Bad: Counts every single matching row
IF (SELECT COUNT(*) FROM logs WHERE level = 'ERROR') > 0 THEN ...
-- Good: Stops after the first match
IF EXISTS (SELECT 1 FROM logs WHERE level = 'ERROR') THEN ...

-- Covered Index: Index on (user_id, status)
-- Database uses only index pages (Index-Only Scan)
SELECT status FROM orders WHERE user_id = 456;
```

### Common Rewrite Table

| Slow Pattern | Fast Rewrite | Rationale |
| :--- | :--- | :--- |
| `SELECT COUNT(*)` (Estimate) | `SELECT reltuples::bigint FROM pg_class WHERE relname = 't'` | Use catalog stats |
| `WHERE col IN (SELECT...)` | `WHERE EXISTS (SELECT 1...)` | Early exit |
| `SELECT DISTINCT a, b` | `GROUP BY a, b` | Faster hashing in some engines |
| `ORDER BY random() LIMIT 1` | `TABLESAMPLE SYSTEM (0.01)` (PG) | Avoids full scan/sort |
| `WHERE YEAR(date) = 2024` | `WHERE date >= '2024-01-01' AND date < '2025-01-01'` | Sargability |
| `SELECT *` | `SELECT col1, col2` | Reduces I/O; index-only scans |

## Correlated Subqueries

Correlated subqueries typically lead to O(n * m) performance because they run for every outer row.

```sql
-- Slow: Correlated Subquery
SELECT p.name, (SELECT SUM(o.amount) FROM orders o WHERE o.product_id = p.id) as total
FROM products p;

-- Fast: LEFT JOIN with GROUP BY
SELECT p.name, SUM(o.amount) as total
FROM products p
LEFT JOIN orders o ON o.product_id = p.id
GROUP BY p.id, p.name;

-- Fast (PostgreSQL): LATERAL JOIN
SELECT p.name, top_orders.amount FROM products p
CROSS JOIN LATERAL (
    SELECT amount FROM orders o WHERE o.product_id = p.id ORDER BY amount DESC LIMIT 3
) as top_orders;
```

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
| :--- | :--- | :--- |
| **SELECT \*** | Unnecessary I/O | Name specific columns |
| **WHERE function(col)** | Prevents index usage | Rewrite condition or use expression index |
| **OR on different cols** | Forces full table scan | Use `UNION ALL` of indexed queries |
| **Implicit Type Cast** | Index bypass | Match parameter types to column types |
| **Missing LIMIT** | Memory exhaustion | Use pagination |
| **LIKE '%pattern'** | No index search | Use Full-Text or Trigram index |
| **ORDER BY in subquery**| Redundant | Order in final outer query |
| **HAVING for filters** | Post-aggregation filter | Use `WHERE` for pre-aggregation filtering |

### Type Casting and Leading Wildcards

```sql
-- Potentially slow if id_str is VARCHAR and index is on VARCHAR
SELECT * FROM users WHERE id_str = 123; -- Implicit cast kills index
SELECT * FROM users WHERE id_str = '123'; -- Proper

-- Leading wildcard prevents index search
SELECT * FROM products WHERE sku LIKE '%123';
-- Use Trigram index (PG): CREATE INDEX trgm_idx ON products USING GIST (sku gist_trgm_ops);
```

## Data Type Optimization for Queries

The choice of data types directly affects query performance by determining the size of the data that must be read from disk and stored in memory.

- **Smallest sufficient type**: Use `SMALLINT` or `INT` instead of `BIGINT` if the range is known. Smaller rows mean more rows per page, increasing cache hits.
- **Fixed vs Variable length**: In some engines (like older MySQL), fixed-length columns (`CHAR`) can be slightly faster to calculate offsets, but modern engines generally handle `VARCHAR` efficiently.
- **UUID vs Serial**: UUIDs are 128-bit and randomly distributed, which leads to index fragmentation and "leaf page splits" in B-tree indexes. If using UUIDs, consider "v7" UUIDs which are time-ordered and more index-friendly.
- **JSONB vs Structured Columns**: While `JSONB` in PostgreSQL is powerful, filtering on top-level columns is always faster than extracting values from a JSON blob. Use `JSONB` for truly dynamic data, not for attributes that are frequently used in `WHERE` clauses.

## Optimization Verification Workflow

Every query optimization attempt should follow a consistent verification process:

1. **Establish a Baseline**: Measure the execution time and resource usage (buffers read/written) before any changes.
2. **Isolate the Bottleneck**: Use `EXPLAIN` to identify if the cost is in the scan (I/O) or the join/aggregate (CPU).
3. **Apply One Change at a Time**: Change an index, a join order, or a rewrite—never all three at once.
4. **Verify with Realistic Data**: A query that is fast on 100 rows may be disastrous on 1,000,000 rows. Use a staging environment with production-like data volume and distribution.
5. **Check for Regressions**: Ensure that adding an index to speed up one query doesn't unacceptably slow down `INSERT` or `UPDATE` operations on that table.



## Final Optimization Checklist

- [ ] Are all JOIN columns indexed?
- [ ] Are all WHERE clauses sargable (no functions on columns)?
- [ ] Is the result set limited via pagination or a reasonable LIMIT?
- [ ] Are we using SELECT only for the columns actually needed?
- [ ] Have we checked for N+1 patterns in the application-to-database interaction?
- [ ] Does the EXPLAIN plan show an Index-Only Scan where possible?
- [ ] For high-volume writes, are we using batch operations (Bulk INSERT/COPY)?
