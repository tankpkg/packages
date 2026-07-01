# Client Library (supabase-js v2)

Sources: supabase-js v2 Reference Documentation, Supabase JavaScript Client GitHub (supabase/supabase-js), PostgREST Documentation (query syntax), Supabase TypeScript Support Guide

Covers: Client initialization, query builder (select, insert, update, delete, upsert), filtering operators, joins via foreign keys, pagination, counting, error handling, TypeScript generics, and realtime subscriptions via the client.

## Client Initialization

### Browser Client

```typescript
import { createClient } from '@supabase/supabase-js';
import type { Database } from '@/types/database';

const supabase = createClient<Database>(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);
```

### Service Role Client (Server Only)

```typescript
const supabaseAdmin = createClient<Database>(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!,
  {
    auth: {
      autoRefreshToken: false,
      persistSession: false,
    },
  }
);
```

The service role key bypasses RLS. Never expose it to the browser.

### Client Options

```typescript
const supabase = createClient<Database>(url, key, {
  auth: {
    autoRefreshToken: true,          // default: true
    persistSession: true,            // default: true
    detectSessionInUrl: true,        // default: true (for OAuth redirects)
    storage: customStorage,          // AsyncStorage for React Native
  },
  global: {
    headers: { 'x-custom-header': 'value' },
    fetch: customFetch,              // custom fetch implementation
  },
  db: {
    schema: 'public',               // default schema
  },
  realtime: {
    params: {
      eventsPerSecond: 10,           // rate limit
    },
  },
});
```

## Query Builder

### SELECT

```typescript
// Select all columns
const { data, error } = await supabase.from('posts').select('*');

// Select specific columns
const { data, error } = await supabase.from('posts').select('id, title, created_at');

// Select with relationship (foreign key join)
const { data, error } = await supabase
  .from('posts')
  .select(`
    id,
    title,
    profiles (
      display_name,
      avatar_url
    )
  `);

// Select with nested relationships
const { data, error } = await supabase
  .from('posts')
  .select(`
    id,
    title,
    profiles ( display_name ),
    comments (
      id,
      body,
      profiles ( display_name )
    )
  `);

// Rename columns in response
const { data } = await supabase
  .from('posts')
  .select('id, title, author:profiles(display_name)');
```

### INSERT

```typescript
// Single row
const { data, error } = await supabase
  .from('posts')
  .insert({ title: 'New Post', user_id: userId, status: 'draft' })
  .select();  // return the inserted row

// Multiple rows
const { data, error } = await supabase
  .from('posts')
  .insert([
    { title: 'Post 1', user_id: userId },
    { title: 'Post 2', user_id: userId },
  ])
  .select();
```

### UPDATE

```typescript
const { data, error } = await supabase
  .from('posts')
  .update({ title: 'Updated Title', status: 'published' })
  .eq('id', postId)
  .select();  // return the updated row
```

Always add a filter (`.eq`, `.in`, etc.) to UPDATE and DELETE queries. Without a filter, the operation applies to all rows matching the RLS policy.

### UPSERT

```typescript
const { data, error } = await supabase
  .from('profiles')
  .upsert(
    { id: userId, display_name: 'New Name', bio: 'Updated bio' },
    { onConflict: 'id' }  // column(s) to match for conflict detection
  )
  .select();
```

### DELETE

```typescript
const { data, error } = await supabase
  .from('posts')
  .delete()
  .eq('id', postId)
  .select();  // return the deleted row
```

## Filtering Operators

### Comparison Operators

| Method | SQL | Example |
|--------|-----|---------|
| `.eq(col, val)` | `= val` | `.eq('status', 'published')` |
| `.neq(col, val)` | `!= val` | `.neq('status', 'deleted')` |
| `.gt(col, val)` | `> val` | `.gt('price', 100)` |
| `.gte(col, val)` | `>= val` | `.gte('created_at', '2024-01-01')` |
| `.lt(col, val)` | `< val` | `.lt('priority', 5)` |
| `.lte(col, val)` | `<= val` | `.lte('priority', 10)` |
| `.is(col, val)` | `IS val` | `.is('deleted_at', null)` |

### Text Operators

| Method | SQL | Example |
|--------|-----|---------|
| `.like(col, pat)` | `LIKE pat` | `.like('title', '%supabase%')` |
| `.ilike(col, pat)` | `ILIKE pat` | `.ilike('title', '%Supabase%')` |
| `.match(query)` | Multiple eq | `.match({ status: 'published', type: 'blog' })` |

### Array/Set Operators

| Method | SQL | Example |
|--------|-----|---------|
| `.in(col, vals)` | `IN (vals)` | `.in('status', ['published', 'featured'])` |
| `.contains(col, val)` | `@> val` | `.contains('tags', ['supabase'])` |
| `.containedBy(col, val)` | `<@ val` | `.containedBy('tags', ['js', 'ts', 'react'])` |
| `.overlaps(col, val)` | `&& val` | `.overlaps('tags', ['react', 'vue'])` |

### Range Operators

| Method | SQL | Example |
|--------|-----|---------|
| `.range(col, val)` | `@> val` | `.range('age_range', '[25,35)')` |

### Logical Operators

```typescript
// OR condition
const { data } = await supabase
  .from('posts')
  .select()
  .or('status.eq.published,status.eq.featured');

// Nested OR with AND
const { data } = await supabase
  .from('posts')
  .select()
  .eq('user_id', userId)
  .or('status.eq.published,status.eq.draft');

// NOT
const { data } = await supabase
  .from('posts')
  .select()
  .not('status', 'eq', 'deleted');
```

## Ordering, Pagination, and Counting

### Ordering

```typescript
const { data } = await supabase
  .from('posts')
  .select()
  .order('created_at', { ascending: false })
  .order('title', { ascending: true });  // secondary sort
```

### Pagination

```typescript
// Offset-based (simple, but slow for large offsets)
const { data } = await supabase
  .from('posts')
  .select()
  .range(0, 9);   // first 10 rows (0-indexed, inclusive)

// Page 2
const { data } = await supabase
  .from('posts')
  .select()
  .range(10, 19);

// Limit
const { data } = await supabase
  .from('posts')
  .select()
  .limit(10);
```

### Keyset Pagination (Recommended for Performance)

```typescript
// First page
const { data: page1 } = await supabase
  .from('posts')
  .select()
  .order('created_at', { ascending: false })
  .limit(10);

// Next page: use last item's cursor
const lastItem = page1[page1.length - 1];
const { data: page2 } = await supabase
  .from('posts')
  .select()
  .order('created_at', { ascending: false })
  .lt('created_at', lastItem.created_at)
  .limit(10);
```

### Counting

```typescript
// Count without fetching rows
const { count, error } = await supabase
  .from('posts')
  .select('*', { count: 'exact', head: true })
  .eq('status', 'published');

// Count with data
const { data, count } = await supabase
  .from('posts')
  .select('*', { count: 'exact' })
  .eq('status', 'published')
  .range(0, 9);
```

Count options: `'exact'` (slow but accurate), `'planned'` (fast estimate), `'estimated'` (exact for small, planned for large).

## Error Handling

```typescript
const { data, error } = await supabase
  .from('posts')
  .select()
  .eq('id', postId)
  .single();  // expect exactly one row

if (error) {
  console.error('Code:', error.code);      // PostgreSQL error code
  console.error('Message:', error.message); // Human-readable message
  console.error('Details:', error.details); // Additional context
  console.error('Hint:', error.hint);       // Suggested fix
  return;
}

// data is typed and non-null here
```

### Common Error Codes

| Code | Meaning | Common Cause |
|------|---------|-------------|
| `PGRST116` | Multiple/no rows for `.single()` | Query matches 0 or 2+ rows |
| `23505` | Unique violation | Duplicate key on insert |
| `23503` | Foreign key violation | Referenced row does not exist |
| `42501` | Insufficient privilege | RLS policy denied access |
| `42P01` | Undefined table | Table name typo or schema mismatch |
| `PGRST301` | JWT expired | Session needs refresh |

### Typed Error Handling Pattern

```typescript
import type { PostgrestError } from '@supabase/supabase-js';

async function getPost(id: string) {
  const { data, error } = await supabase
    .from('posts')
    .select('*')
    .eq('id', id)
    .single();

  if (error) throw new AppError(error);
  return data; // fully typed Post
}

class AppError extends Error {
  code: string;
  constructor(pgError: PostgrestError) {
    super(pgError.message);
    this.code = pgError.code;
  }
}
```

## Calling Database Functions

```typescript
// Simple RPC call
const { data, error } = await supabase.rpc('search_posts', {
  search_term: 'supabase',
});

// RPC with chaining (function returns a table)
const { data, error } = await supabase
  .rpc('get_posts_by_status', { target_status: 'published' })
  .select('id, title')
  .order('created_at', { ascending: false })
  .limit(10);
```

## Single Row Queries

```typescript
// .single() -- expects exactly 1 row (errors on 0 or 2+)
const { data, error } = await supabase
  .from('profiles')
  .select()
  .eq('id', userId)
  .single();

// .maybeSingle() -- expects 0 or 1 row (null if 0, errors on 2+)
const { data, error } = await supabase
  .from('profiles')
  .select()
  .eq('id', userId)
  .maybeSingle();
```

Use `.single()` when the row must exist (fetching current user's profile). Use `.maybeSingle()` when absence is expected (checking if a record exists).

## Abort / Timeout

```typescript
const controller = new AbortController();

// Cancel after 5 seconds
setTimeout(() => controller.abort(), 5000);

const { data, error } = await supabase
  .from('posts')
  .select()
  .abortSignal(controller.signal);
```

## Type Helpers

```typescript
import type { Database } from '@/types/database';

// Table row types
type Post = Database['public']['Tables']['posts']['Row'];
type NewPost = Database['public']['Tables']['posts']['Insert'];
type PostUpdate = Database['public']['Tables']['posts']['Update'];

// Enum types
type PostStatus = Database['public']['Enums']['post_status'];

// Function types
type SearchResult = Database['public']['Functions']['search_posts']['Returns'];
```

For `select()` with specific columns, TypeScript infers the narrowed type automatically when using generated types.
