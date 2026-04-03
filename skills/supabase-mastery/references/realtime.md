# Realtime

Sources: Supabase Realtime Documentation (2024-2026), Supabase Realtime GitHub Repository (supabase/realtime), supabase-js v2 Realtime Reference, Supabase Blog (Realtime Multiplayer Edition)

Covers: Postgres Changes (database event subscriptions), Broadcast (client-to-client messaging), Presence (online user tracking), channel management, filtering, RLS interaction, and performance considerations.

## Realtime Architecture

Supabase Realtime is a globally distributed Elixir server that provides three features over WebSocket connections:

| Feature | Mechanism | Use Case |
|---------|-----------|----------|
| Postgres Changes | Listens to PostgreSQL logical replication | Database INSERT/UPDATE/DELETE notifications |
| Broadcast | Direct message relay between clients | Chat, cursors, game events, custom notifications |
| Presence | Tracks connected client state via CRDT | Online indicators, typing status, active users |

All three features use the same channel abstraction. A single channel can combine Postgres Changes, Broadcast, and Presence subscriptions.

## Postgres Changes

### Subscribe to Table Changes

```typescript
const channel = supabase
  .channel('posts-changes')
  .on(
    'postgres_changes',
    {
      event: '*',           // 'INSERT' | 'UPDATE' | 'DELETE' | '*'
      schema: 'public',
      table: 'posts',
    },
    (payload) => {
      console.log('Change:', payload.eventType);
      console.log('New:', payload.new);
      console.log('Old:', payload.old);
    }
  )
  .subscribe();
```

### Filter Changes

```typescript
// Only receive changes for a specific user
const channel = supabase
  .channel('my-posts')
  .on(
    'postgres_changes',
    {
      event: 'INSERT',
      schema: 'public',
      table: 'posts',
      filter: 'user_id=eq.550e8400-e29b-41d4-a716-446655440000',
    },
    (payload) => handleNewPost(payload.new)
  )
  .subscribe();
```

### Available Filters

| Operator | Syntax | Example |
|----------|--------|---------|
| Equals | `column=eq.value` | `status=eq.published` |
| Not equals | `column=neq.value` | `status=neq.deleted` |
| Less than | `column=lt.value` | `priority=lt.5` |
| Less than or equal | `column=lte.value` | `priority=lte.5` |
| Greater than | `column=gt.value` | `priority=gt.0` |
| Greater than or equal | `column=gte.value` | `priority=gte.1` |
| In list | `column=in.(a,b,c)` | `status=in.(published,featured)` |

### Receiving Old Records on UPDATE/DELETE

By default, `payload.old` only contains `{ id }`. To receive full old records, set the replica identity:

```sql
-- Receive full old record on UPDATE and DELETE
alter table public.posts replica identity full;
```

Use `replica identity full` selectively -- it increases WAL (Write-Ahead Log) size for that table.

### Enable Table for Realtime

Tables must be added to the `supabase_realtime` publication:

```sql
-- Add table to realtime publication
alter publication supabase_realtime add table public.posts;

-- Or via Dashboard: Database > Replication > Add table
```

### RLS and Postgres Changes

Postgres Changes respects RLS policies. The subscribing user's JWT is used to evaluate SELECT policies. If a user's SELECT policy would exclude a row, they will not receive the change event for that row.

This means:
- Users only receive events for rows they can SELECT
- If RLS denies access, the event is silently filtered
- Anonymous users receive events only if an `anon` SELECT policy exists

## Broadcast

Low-latency client-to-client messaging. Messages are not persisted -- clients must be connected to receive them.

### Send and Receive Messages

```typescript
// Subscribe to broadcast events
const channel = supabase
  .channel('room-1')
  .on('broadcast', { event: 'cursor-move' }, (payload) => {
    console.log('Cursor:', payload.payload);
  })
  .subscribe();

// Send a broadcast message
channel.send({
  type: 'broadcast',
  event: 'cursor-move',
  payload: { x: 100, y: 200, userId: 'user-123' },
});
```

### Broadcast Options

```typescript
const channel = supabase.channel('room-1', {
  config: {
    broadcast: {
      self: true,   // receive own messages (default: false)
      ack: true,    // wait for server acknowledgment (default: false)
    },
  },
});
```

### Broadcast Use Cases

| Feature | Event Type | Payload |
|---------|-----------|---------|
| Cursor tracking | `cursor-move` | `{ x, y, userId }` |
| Typing indicator | `typing` | `{ userId, isTyping }` |
| Chat message | `message` | `{ text, userId, timestamp }` |
| Game event | `player-action` | `{ action, data }` |
| Notification | `notification` | `{ type, message }` |

## Presence

Track and synchronize shared state across connected clients. State syncs automatically via CRDTs (Conflict-free Replicated Data Types).

### Track User Presence

```typescript
const channel = supabase.channel('online-users');

// Listen for presence changes
channel
  .on('presence', { event: 'sync' }, () => {
    const state = channel.presenceState();
    console.log('Online users:', Object.keys(state).length);
  })
  .on('presence', { event: 'join' }, ({ key, newPresences }) => {
    console.log('Joined:', key, newPresences);
  })
  .on('presence', { event: 'leave' }, ({ key, leftPresences }) => {
    console.log('Left:', key, leftPresences);
  })
  .subscribe(async (status) => {
    if (status === 'SUBSCRIBED') {
      await channel.track({
        user_id: currentUser.id,
        display_name: currentUser.name,
        online_at: new Date().toISOString(),
      });
    }
  });
```

### Update Presence State

```typescript
// Update tracked state (e.g., user started typing)
await channel.track({
  user_id: currentUser.id,
  display_name: currentUser.name,
  status: 'typing',
});
```

### Untrack (Go Offline)

```typescript
await channel.untrack();
```

### Presence State Structure

```typescript
// channel.presenceState() returns:
{
  "user-123": [
    {
      user_id: "user-123",
      display_name: "Jane",
      online_at: "2024-01-15T10:30:00Z",
      presence_ref: "abc123"  // unique per connection
    }
  ],
  "user-456": [
    {
      user_id: "user-456",
      display_name: "John",
      online_at: "2024-01-15T10:31:00Z",
      presence_ref: "def456"
    }
  ]
}
```

A user can have multiple entries if connected from multiple devices.

## Channel Management

### Subscribing

```typescript
const channel = supabase.channel('my-channel');

channel.subscribe((status, err) => {
  if (status === 'SUBSCRIBED') {
    console.log('Connected!');
  }
  if (status === 'CHANNEL_ERROR') {
    console.error('Channel error:', err);
  }
  if (status === 'TIMED_OUT') {
    console.warn('Connection timed out');
  }
  if (status === 'CLOSED') {
    console.log('Channel closed');
  }
});
```

### Unsubscribing

```typescript
// Remove specific channel
supabase.removeChannel(channel);

// Remove all channels
supabase.removeAllChannels();
```

### Combining Features on One Channel

```typescript
const channel = supabase
  .channel('room-1')
  // Postgres Changes
  .on('postgres_changes', {
    event: 'INSERT',
    schema: 'public',
    table: 'messages',
    filter: `room_id=eq.${roomId}`,
  }, handleNewMessage)
  // Broadcast
  .on('broadcast', { event: 'typing' }, handleTyping)
  // Presence
  .on('presence', { event: 'sync' }, handlePresenceSync)
  .subscribe();
```

## Cleanup Patterns

### React useEffect Cleanup

```typescript
useEffect(() => {
  const channel = supabase
    .channel('posts')
    .on('postgres_changes', {
      event: '*',
      schema: 'public',
      table: 'posts',
    }, handleChange)
    .subscribe();

  return () => {
    supabase.removeChannel(channel);
  };
}, []);
```

### Next.js Client Component

```typescript
'use client';
import { useEffect, useState } from 'react';
import { createBrowserClient } from '@supabase/ssr';

export function RealtimeMessages({ roomId }: { roomId: string }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const supabase = createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );

  useEffect(() => {
    const channel = supabase
      .channel(`room-${roomId}`)
      .on('postgres_changes', {
        event: 'INSERT',
        schema: 'public',
        table: 'messages',
        filter: `room_id=eq.${roomId}`,
      }, (payload) => {
        setMessages((prev) => [...prev, payload.new as Message]);
      })
      .subscribe();

    return () => { supabase.removeChannel(channel); };
  }, [roomId, supabase]);

  return <>{/* render messages */}</>;
}
```

## Performance Considerations

| Factor | Recommendation |
|--------|---------------|
| Channel count | Minimize unique channels -- combine features on shared channels |
| Filter specificity | Use specific filters to reduce unnecessary event delivery |
| Payload size | Keep broadcast payloads small (<1KB). Large data goes in DB, send ID via broadcast |
| Presence state | Track minimal state. Do not put entire user profiles in presence |
| Replica identity | Use `full` only on tables where old record data is needed |
| Publication scope | Add only tables that need realtime to `supabase_realtime` publication |
| Unsubscribe | Always clean up channels on component unmount to avoid memory leaks |
| Reconnection | supabase-js handles reconnection automatically. Monitor `CHANNEL_ERROR` for debugging |

## Quotas and Limits

| Resource | Free Plan | Pro Plan |
|----------|-----------|----------|
| Concurrent connections | 200 | 500 (pooled) |
| Messages per second | 100 | 500 |
| Channel joins per second | 100 | 500 |
| Message size | 1MB | 3MB |
| Presence key count | 100 per channel | 100 per channel |

Exceed limits and the server drops the connection. Design for graceful degradation.
