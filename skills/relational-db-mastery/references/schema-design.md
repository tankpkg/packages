# Schema Design for Performance

Sources: Karwin (SQL Antipatterns), Kleppmann (Designing Data-Intensive Applications), PostgreSQL/MySQL documentation

Covers: normalization tradeoffs, data type selection, partitioning, temporal patterns, schema anti-patterns.

## Normalization Quick Reference

Normalization is the process of organizing the columns and tables of a relational database to minimize data redundancy and improve data integrity. It is an engineering discipline that ensures every piece of data is stored in exactly one place, which prevents inconsistency during updates.

### The Standard Normal Forms (NF)

| Normal Form | Rule | Practical Meaning |
| :--- | :--- | :--- |
| **1st Normal Form (1NF)** | Eliminate repeating groups in individual tables. Create a separate table for each set of related data. Identify each set of related data with a primary key. | No arrays-in-columns, no col1/col2/col3 patterns. Each cell holds exactly one atomic value. |
| **2nd Normal Form (2NF)** | 1NF + remove subsets of data that apply to multiple rows of a table and place them in separate tables. Create relationships between these new tables and their predecessors through the use of foreign keys. | Every non-key column must depend on the WHOLE primary key. This is only relevant for tables with composite keys. |
| **3rd Normal Form (3NF)** | 2NF + remove columns that are not dependent upon the primary key. | Non-key columns must not depend on other non-key columns. This eliminates "transitive dependencies." |
| **Boyce-Codd Normal Form (BCNF)** | Every determinant must be a candidate key. | A stricter version of 3NF that handles overlapping candidate keys, preventing rare update anomalies. |

### Case Study: Normalizing a Table

**Initial State (Unnormalized)**:
| OrderID | CustomerName | CustomerCity | Items |
| :--- | :--- | :--- | :--- |
| 101 | Alice | New York | Apples (2), Oranges (5) |
| 102 | Bob | Chicago | Bananas (10) |

**1st Normal Form (Atomicity)**:
Move items to their own table or split the comma-separated list.
| OrderID | Item | Quantity |
| :--- | :--- | :--- |
| 101 | Apples | 2 |
| 101 | Oranges | 5 |
| 102 | Bananas | 10 |

**2nd Normal Form (Whole Key)**:
Ensure non-key columns depend on the whole key. If the key is `(OrderID, Item)`, then `ItemCategory` shouldn't be here if it only depends on `Item`.
- Move `ItemCategory` to a `Products` table.

**3rd Normal Form (Non-Transitive)**:
In the `Orders` table, `CustomerCity` depends on `CustomerName`, which depends on `OrderID`.
- Move `CustomerName` and `CustomerCity` to a `Customers` table.

## When to Denormalize

Denormalization is a strategy used on a previously-normalized database to increase performance. In a denormalized database, redundant data is added to speed up complex queries.

### Denormalization Patterns

#### 1. Materialized Views
In PostgreSQL, a materialized view stores the result of a query physically on disk. It is ideal for dashboards that require complex aggregations across multiple tables.
```sql
CREATE MATERIALIZED VIEW monthly_sales_report AS
SELECT 
    date_trunc('month', o.created_at) as month,
    p.category,
    SUM(oi.quantity * oi.price) as total_revenue
FROM orders o
JOIN order_items oi ON o.id = oi.order_id
JOIN products p ON oi.product_id = p.id
WHERE o.status = 'completed'
GROUP BY 1, 2;

-- Maintenance
CREATE UNIQUE INDEX idx_monthly_sales ON monthly_sales_report(month, category);
REFRESH MATERIALIZED VIEW CONCURRENTLY monthly_sales_report;
```

#### 2. Summary and Counter Tables
Maintain a dedicated table for counts to avoid expensive `COUNT(*)` operations.
```sql
CREATE TABLE product_stats (
    product_id BIGINT PRIMARY KEY REFERENCES products(id),
    total_orders BIGINT DEFAULT 0,
    average_rating NUMERIC(3, 2) DEFAULT 0.0
);
```

#### 3. Redundant Column Pattern
Storing a piece of data from a parent table in a child table to avoid a JOIN. For example, storing the `customer_email` in the `orders` table.

## Data Type Selection

Choosing the smallest data type that can safely hold your data is a fundamental performance optimization.

### Primary and Foreign Key Types

| Type | Size | Range | Recommended Use |
| :--- | :--- | :--- | :--- |
| **BIGINT** | 8 bytes | 9.2 Quintillion | Default for Primary Keys. |
| **INTEGER** | 4 bytes | 2.1 Billion | Small lookup tables. |
| **UUID** | 16 bytes | N/A | Distributed systems. |

### The UUIDv7 Performance Advantage
Random UUIDv4 values cause index fragmentation. UUIDv7 includes a timestamp at the beginning, making the values sequential. This allows the database to append to the B-tree index, maintaining high performance while preserving uniqueness.

### The Dual-ID Pattern

Use internal serial for JOINs and external UUID for APIs:
```sql
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    public_id UUID DEFAULT gen_random_uuid() UNIQUE NOT NULL,
    email TEXT NOT NULL
);
-- Internal JOINs use id (8 bytes, fast)
-- API exposes public_id (secure, unpredictable)
```

### String Types

| Type | PostgreSQL Behavior | MySQL Behavior | Use When |
| :--- | :--- | :--- | :--- |
| **VARCHAR(n)** | Same as TEXT with length check | Stored inline up to row limit | Need max length validation |
| **TEXT** | Identical performance to VARCHAR | Stored off-page if large | No length constraint needed |
| **CHAR(n)** | Padded with spaces, rarely useful | Fixed-width storage | Fixed-length codes (ISO country) |

In PostgreSQL, `VARCHAR` and `TEXT` have identical storage and performance. Prefer `TEXT` unless you need a length constraint.

### Timestamp Types

Always use `TIMESTAMPTZ` (timestamp with time zone) over `TIMESTAMP`:
- `TIMESTAMPTZ` stores as UTC internally, converts to client timezone on retrieval
- `TIMESTAMP` (without tz) stores the literal value — timezone bugs in every multi-timezone app
- Both are 8 bytes in PostgreSQL — no storage difference

### Financial and Exact Data
- **NUMERIC**: Use for money. Specify precision and scale: `NUMERIC(19, 4)`.
- **FLOAT/DOUBLE**: Never use for money due to rounding errors. Use only for scientific data.

### JSONB vs Normalized Columns

| Signal | Choose | Why |
| :--- | :--- | :--- |
| Schema varies per row | JSONB | Flexible document storage |
| All rows have same fields | Normalized columns | Type safety, constraints, indexes |
| Need to query/filter by field frequently | Normalized columns | Direct index support, faster WHERE |
| Rarely queried, just stored and returned | JSONB | Simpler schema, fewer migrations |
| Need database constraints/validation | Normalized columns | CHECK, NOT NULL, FK constraints |
| Flexible metadata/user preferences | JSONB | Schema doesn't need migration |
| Nested data with unknown depth | JSONB | Natural document structure |
| Write-heavy path updating single fields | Normalized columns | JSONB rewrites entire document |

```sql
-- JSONB with GIN index for flexible queries
ALTER TABLE products ADD COLUMN attributes JSONB DEFAULT '{}';
CREATE INDEX idx_product_attrs ON products USING gin(attributes jsonb_path_ops);

-- Query: products with color = 'red'
SELECT * FROM products WHERE attributes @> '{"color": "red"}';
```

### Enum vs Text with CHECK

| Approach | Pros | Cons |
| :--- | :--- | :--- |
| **PostgreSQL ENUM** | 4 bytes, type safety | Hard to modify (requires migration), can't reorder |
| **TEXT + CHECK** | Easy to modify, standard SQL | No compile-time safety |
| **Lookup table + FK** | Full relational integrity, metadata | Extra JOIN needed |

Prefer `TEXT + CHECK` for most cases:
```sql
CREATE TABLE orders (
    status TEXT NOT NULL CHECK (status IN ('pending', 'shipped', 'delivered', 'cancelled'))
);
```

## Table Partitioning

Partitioning splits one logically large table into many smaller physical tables (partitions).

### Strategies
1. **Range Partitioning**: Divide by time ranges (e.g., month, year).
2. **List Partitioning**: Divide by specific values (e.g., `country_code`).
3. **Hash Partitioning**: Divide by a hash of the key to evenly distribute load.

```sql
-- Range Partitioning by Year
CREATE TABLE sensor_data (
    id BIGSERIAL,
    value NUMERIC,
    created_at TIMESTAMPTZ NOT NULL
) PARTITION BY RANGE (created_at);

CREATE TABLE sensor_data_2023 PARTITION OF sensor_data
    FOR VALUES FROM ('2023-01-01') TO ('2024-01-01');
```

### When Partitioning Helps vs Hurts

| Helps | Hurts |
| :--- | :--- |
| Queries always filter on partition key | Queries span all partitions |
| Individual partitions fit in memory | Small tables (overhead not worth it) |
| Need to drop old data fast (drop partition) | Cross-partition JOINs needed frequently |
| Table > 10M rows with clear partition key | No obvious partition key exists |
| Time-series with retention policy | Random access patterns across all data |

## Recursive Data Patterns

Handling hierarchies (trees) in a relational database requires choosing a pattern based on read vs. write performance.

| Pattern | Description | Performance |
| :--- | :--- | :--- |
| **Adjacency List** | Store `parent_id` on each row. | Fast writes. Slow reads (requires Recursive CTEs). |
| **Path Enumeration** | Store path like `/1/4/22/`. | Fast reads with `LIKE`. Brittle to moves. |
| **Nested Sets** | Store `left` and `right` bounds. | Very fast reads. Extremely slow writes. |
| **Closure Table** | Separate table for all relationships. | Most flexible. High storage cost. |

```sql
WITH RECURSIVE subordinates AS (
    SELECT id, name, manager_id FROM employees WHERE id = 1
    UNION ALL
    SELECT e.id, e.name, e.manager_id 
    FROM employees e 
    JOIN subordinates s ON s.id = e.manager_id
)
SELECT * FROM subordinates;
```

## Temporal Data Patterns

Temporal schemas track data as it changes over time, allowing for "as of" queries.

### 1. Slowly Changing Dimensions (SCD)
- **Type 2**: Add a new row for every change with `valid_from` and `valid_to`.
- **Type 4**: Store current data in one table and history in another.

### 2. Bi-temporal Modeling
Tracks two timelines: **Valid Time** (when the fact happened) and **System Time** (when the record was saved). Critical for auditing corrections.

### 3. Soft Deletes
Adding a `deleted_at` timestamp. Always use a **Partial Index** to exclude deleted rows.
```sql
CREATE INDEX idx_active_users ON users(email) WHERE deleted_at IS NULL;
```

## Database Sharding vs. Partitioning

### Sharding (Horizontal Partitioning)
Sharding involves splitting rows across multiple database servers.
- **Shard Key**: The column used to determine which shard a row belongs to (e.g., `user_id`).
- **Complexity**: Requires a shard coordinator or application-level routing.
- **Benefit**: Unlimited horizontal scale for storage and I/O.

### Vertical Partitioning
Vertical partitioning involves splitting a table into two tables with a 1:1 relationship based on column usage.
- **Scenario**: A `users` table has many columns, but `bio`, `preferences`, and `settings` are rarely accessed compared to `username` and `email`.
- **Performance**: Splitting these into `users` and `user_profiles` allows the `users` table to remain "narrow," meaning more rows fit into each disk page.

## Schema Anti-Patterns

### 1. Jaywalking (Comma-Separated Lists)
Storing IDs in a string column. No integrity, no indexing.
- **Fix**: Use a many-to-many Join Table.

### 2. Entity-Attribute-Value (EAV)
Using a generic table for all data. Slow, complex, no type safety.
- **Fix**: Use `JSONB` or proper normalized tables.

### 3. Metadata Tribbles
Creating tables like `orders_2023`, `orders_2024` manually.
- **Fix**: Use native Table Partitioning.

### 4. Polymorphic Associations
A table referencing multiple tables via a `type` column. No referential integrity.
- **Fix**: Use separate join tables or an interface table.

### 5. God Tables
Tables with 50+ columns where most are NULL for any given row. Wide rows waste space and I/O.
- **Fix**: Split into related tables with 1:1 or 1:many relationships.

### 6. Implicit NULL Semantics
Using NULL to mean both "unknown" and "not applicable." Leads to query bugs.
- **Fix**: Use separate columns or explicit status values.

### 7. String-Typed Dates
Storing dates as `VARCHAR`. No validation, no date functions, lexicographic sort breaks.
- **Fix**: Use `DATE`, `TIMESTAMP`, or `TIMESTAMPTZ`.

### 8. Missing Foreign Key Constraints
No FK means orphan rows accumulate silently. Data integrity degrades over time.
- **Fix**: Always add `FOREIGN KEY` constraints. Always index FK columns manually in PostgreSQL.

## Constraint Performance

1. **NOT NULL**: Allows the engine to skip null-handling paths.
2. **CHECK**: `CHECK (price > 0)` allows the optimizer to skip the table if a query asks for `price < 0` (Constraint Exclusion).
3. **FOREIGN KEY**: PostgreSQL does not automatically index foreign keys. Always add these indexes manually.

## Database Maintenance and Schema Tuning

### Heap Only Tuples (HOT)
PostgreSQL's HOT updates reduce index bloat by allowing row updates to stay on the same data page. This is triggered when:
- The update doesn't change any indexed columns.
- There is enough free space on the page (controlled by the `FILLFACTOR` setting).

### Column Alignment
PostgreSQL pads columns to align with CPU architecture boundaries (usually 8 bytes).
- **Rule**: Place large, fixed-width columns first (`BIGINT`, `TIMESTAMP`), then smaller types (`INT`, `SMALLINT`), then variable-width types (`TEXT`, `JSONB`).
- **Impact**: On a table with 100 million rows, proper column ordering can save 10-15% of total disk space.

## Advanced PostgreSQL Specific Types

| Type | Purpose | Performance Benefit |
| :--- | :--- | :--- |
| **CITEXT** | Case-insensitive text | Eliminates the need for `LOWER(email)` calls and associated functional indexes. |
| **HSTORE** | Simple Key-Value storage | Faster than JSONB for simple, non-nested string-to-string mappings. |
| **LTREE** | Hierarchical path storage | Optimized for "path enumeration" queries using specialized GIST indexes. |
| **MACADDR** | Ethernet MAC address | More storage-efficient (6 bytes) and validated than storing as TEXT. |
| **TSVECTOR** | Full-text search | Optimized for high-speed keyword searches with GIN indexes. |

## Data Archiving and Cold Storage

As data grows, the "active" data set should remain small to fit in RAM.
1. **The Partitioning Strategy**: Move older partitions to slower storage.
2. **The "Shadow" Table Strategy**: Periodically move old rows from `orders` to `orders_history`.
3. **The Logical Export Strategy**: Move old data to an object store (S3) and delete it from the database.

## Schema Versioning Best Practices

- **Avoid SELECT ***: Always specify columns in application code to avoid breaking when columns are added.
- **Add Columns as Nullable**: Adding a `NOT NULL` column with a default value to a large table requires a full table rewrite in many databases. Add as nullable, backfill data, then add the constraint.
- **Use Migration Tools**: Use `Flyway`, `Liquibase`, or framework-specific tools (Rails, Django) to ensure schema changes are versioned and reproducible.
- **Online Schema Changes**: For high-traffic databases, use tools like `gh-ost` or `pt-online-schema-change` to avoid long table locks during migrations.
