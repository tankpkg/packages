# Agent Memory Systems

Sources: DohkoAI (8 AI Agent Memory Patterns, 2025), CrewAI (Memory Documentation, 2025), LangChain (Memory Documentation, 2025), Mem0 (Documentation, 2025), Anthropic (Context Window Management, 2024), 2026 production patterns research

Covers: sliding window with summarization, semantic memory (vector), episodic memory, working memory, memory consolidation, persistence, unified memory management, and production implementation patterns.

## Memory Architecture Overview

Agents need multiple memory systems working together, mirroring how human cognition separates immediate recall, working memory, and long-term storage.

| Layer | Pattern | What It Stores | Lifetime |
|-------|---------|----------------|----------|
| Immediate | Sliding window | Last N messages + running summary | Current session |
| Short-term | Working memory | Current task state, plan, hypotheses | Current task |
| Long-term | Semantic memory | Facts, preferences, knowledge | Persistent |
| Experiential | Episodic memory | Past task outcomes and lessons | Persistent |
| Maintenance | Consolidation | Merge duplicates, decay unused | Between sessions |

## 1. Sliding Window with Summarization

The baseline memory pattern. Maintain recent messages in full; summarize older messages to stay within token budget. Every agent needs this.

### Implementation Strategy

```
Token budget: 8000 tokens for memory
Threshold: when usage exceeds 80%, trigger compression
Compression: summarize oldest half of messages
Summarizer: use fast/cheap model (Haiku, GPT-4o-mini) — not your main model
```

### Summarization Prompt Template

```
Previous summary: {existing_summary}

New messages to incorporate:
{old_messages}

Create a concise summary preserving:
- Key decisions made
- User preferences expressed
- Task progress and milestones
- Important facts and constraints
- Action items and commitments
```

### Sliding Window Trade-offs

| Window Size | Memory Cost | Recall Quality | Summarization Frequency |
|-------------|------------|----------------|------------------------|
| 2K tokens | Low | Recent only | Frequent (every 4-6 messages) |
| 8K tokens | Medium | Good balance | Moderate (every 15-20 messages) |
| 32K tokens | High | Excellent | Rare |
| Full context | Maximum | Complete | Never |

### Best Practice

Set window size to 20-30% of total context window. Reserve the rest for system prompt, tools, and agent reasoning. Summarize aggressively — models handle summaries well.

## 2. Working Memory (Structured Scratchpad)

A structured object tracking the current task state. Think of it as the agent's whiteboard — visible at each step, helping the model maintain focus.

### Schema

```typescript
interface WorkingMemory {
  goal: string;                    // What the agent is trying to accomplish
  plan: string[];                  // Ordered steps to reach the goal
  currentStep: number;             // Index into plan
  findings: Record<string, any>;   // Key-value pairs of discovered information
  hypotheses: Array<{
    text: string;
    confidence: number;            // 0-1
    status: "untested" | "confirmed" | "rejected";
  }>;
  blockers: string[];              // What's preventing progress
  decisions: Array<{
    decision: string;
    reasoning: string;
    timestamp: string;
  }>;
  scratch: string;                 // Free-form notes
}
```

### Injection Pattern

Serialize working memory into a labeled context block and include it in every agent prompt:

```
# Working Memory

**Goal:** Debug payment webhook failure
**Plan:**
  [done] 1. Check webhook logs
  [current] 2. Verify API key status
  3. Test with fresh key
  4. Confirm fix in staging

**Findings:**
  - webhook_error: "403 Forbidden from Stripe"
  - last_success: "2025-12-01T14:30:00Z"

**Hypotheses:**
  - [untested] API key expired (confidence: 0.7)
```

### When to Use Working Memory

| Scenario | Without Working Memory | With Working Memory |
|----------|----------------------|---------------------|
| Multi-step debugging | Agent loses track of what it tried | Structured hypothesis tracking |
| Research tasks | Re-searches same topics | Records findings, avoids repeats |
| Planning tasks | Forgets plan mid-execution | Plan visible at each step |
| Any task > 5 steps | Context drift, redundant work | Goal + progress always visible |

## 3. Semantic Memory (Vector-Based Long-Term)

Store facts as embeddings and retrieve by semantic similarity. Goes beyond basic RAG by adding importance scoring, duplicate detection, recency weighting, and garbage collection.

### Key Design Decisions

| Decision | Recommendation | Reasoning |
|----------|---------------|-----------|
| Embedding model | text-embedding-3-small | Good quality, low cost, fast |
| Vector store | Depends on scale | SQLite/pgvector for < 100K, Pinecone/Qdrant for > 100K |
| Similarity metric | Cosine similarity | Standard, works well for text |
| Duplicate threshold | 0.92-0.95 cosine similarity | Below 0.92 may merge distinct items |
| Categories | fact, preference, decision, lesson | Enables filtered retrieval |

### Scoring Formula

Rank retrieved memories by combining relevance, importance, and recency:

```
score = (similarity * 0.6) + (importance * 0.25) + (recency * 0.15)
```

- **Similarity** (0.6 weight): How close the embedding is to the query
- **Importance** (0.25 weight): Manually or automatically assigned 0-1 score
- **Recency** (0.15 weight): Decays over time (linear decay over 30 days)

### Automatic Importance Assignment

| Signal | Importance |
|--------|-----------|
| Explicit user preference ("I always want...") | 0.9 |
| User correction of agent behavior | 0.8 |
| Key decision with reasoning | 0.7 |
| Factual information from tools | 0.5 |
| Casual conversation detail | 0.3 |
| Auto-extracted from assistant response | 0.4 |

### Garbage Collection

Run between sessions to prevent unbounded growth:

```
Remove memory if ALL of these are true:
  - Importance < 0.3
  - Access count < 2
  - Age > 30 days
```

## 4. Episodic Memory (Experience-Based)

Store complete task episodes with their outcomes and lessons learned. When the agent encounters a similar situation, it recalls how past episodes unfolded.

### Episode Structure

```typescript
interface Episode {
  id: string;
  title: string;                // "Debug payment webhook failure"
  startedAt: Date;
  endedAt: Date | null;
  events: Array<{
    type: string;               // "investigation", "hypothesis", "action", "verification"
    description: string;
    timestamp: Date;
    data?: Record<string, any>;
  }>;
  outcome: "success" | "failure" | "partial" | "abandoned";
  lessons: string[];            // Extracted insights for future use
  tags: string[];               // For retrieval: ["debugging", "payments", "webhook"]
}
```

### Episode Lifecycle

```
1. START    — Agent begins a new task → create episode with title and tags
2. RECORD   — Each significant action → add event to episode
3. CLOSE    — Task completes → set outcome, extract lessons
4. RETRIEVE — Similar situation arises → search episodes by similarity to current situation
5. INJECT   — Add relevant episode narratives to agent context
```

### Lesson Extraction Prompt

```
Task: {episode.title}
Events: {episode.events}
Outcome: {episode.outcome}

Extract 2-4 concise lessons that would help in similar future situations.
Focus on: what worked, what didn't, what to try differently.
Format: bullet points, imperative voice.
```

### Episodic vs Semantic Memory

| Dimension | Semantic | Episodic |
|-----------|----------|----------|
| Stores | Individual facts | Complete task sequences |
| Retrieval | By content similarity | By situation similarity |
| Value | Knowledge recall | Experience-based guidance |
| Growth | Continuous (every interaction) | Per-task (one episode per task) |
| Use when | Need specific facts | Need experiential guidance |

## 5. Memory Consolidation

Run between sessions to maintain memory quality. Analogous to sleep-based memory consolidation in humans.

### Consolidation Steps

```
1. MERGE DUPLICATES   — Find memories with > 0.92 cosine similarity, keep highest-importance
2. EXTRACT PATTERNS   — Convert recent episode lessons into semantic memories
3. DECAY UNUSED       — Reduce importance of unaccessed memories by 20%
4. PROMOTE FREQUENT   — Increase importance of frequently accessed memories by 20%
5. GARBAGE COLLECT    — Remove low-importance, old, unaccessed memories
```

### Consolidation Schedule

| Trigger | Action |
|---------|--------|
| Session end | Run full consolidation |
| Memory count > threshold | Run garbage collection only |
| After significant task completion | Extract and store lessons |
| Weekly maintenance | Full consolidation + integrity check |

## 6. Persistence Layer

All memory types need persistence across restarts. Choose storage based on scale.

### Storage Recommendations

| Scale | Storage | Reasoning |
|-------|---------|-----------|
| Single agent, < 10K memories | SQLite | Zero-config, embedded, handles concurrent reads |
| Single agent, vector search needed | SQLite + pgvector | Add vector search without external deps |
| Multi-agent, shared memory | PostgreSQL + pgvector | Concurrent writes, shared state |
| High-scale, distributed | Redis (vector search) + PostgreSQL | Sub-millisecond retrieval, separate persistence |
| Managed service | Mem0, Zep | Handles embedding, retrieval, consolidation |

### Schema Design (SQLite)

```sql
CREATE TABLE memories (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    category TEXT NOT NULL,         -- "fact", "preference", "decision", "lesson"
    importance REAL DEFAULT 0.5,
    embedding BLOB,
    created_at TEXT NOT NULL,
    last_accessed TEXT NOT NULL,
    access_count INTEGER DEFAULT 0,
    source TEXT DEFAULT '',
    metadata TEXT DEFAULT '{}'
);

CREATE TABLE episodes (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    outcome TEXT DEFAULT '',
    events TEXT DEFAULT '[]',       -- JSON array
    lessons TEXT DEFAULT '[]',      -- JSON array
    tags TEXT DEFAULT '[]'          -- JSON array
);

CREATE INDEX idx_memories_category ON memories(category);
CREATE INDEX idx_memories_importance ON memories(importance);
CREATE INDEX idx_episodes_tags ON episodes(tags);
```

## 7. Unified Memory Manager

Single interface that coordinates all memory subsystems.

### Manager Responsibilities

```
process_message(role, content):
  1. Add to sliding window
  2. Auto-extract facts from assistant responses → semantic memory
  3. Update working memory if task-relevant

get_full_context(query, task_type):
  1. Retrieve sliding window messages
  2. Query semantic memory for relevant facts
  3. Search episodic memory for similar past situations
  4. Serialize working memory
  5. Assemble into prioritized context block

end_session():
  1. Close current episode (if open)
  2. Run consolidation
  3. Persist all state
```

### Context Budget Allocation

| Component | Budget % | Priority |
|-----------|----------|----------|
| System prompt + tools | 30-40% | Fixed (always present) |
| Sliding window (recent messages) | 25-35% | High |
| Working memory | 10-15% | High (current task) |
| Semantic memory retrieval | 10-15% | Medium |
| Episodic memory retrieval | 5-10% | Low (only when relevant) |

### Context-Aware Retrieval

Adapt retrieval strategy based on task type:

| Task Type | Priority Memories | Lower Priority |
|-----------|-------------------|----------------|
| Debugging | Episodic (past fixes), semantic (error patterns) | Preferences |
| Creating | Preferences, style examples | Past episodes |
| Analyzing | Semantic (domain facts), working memory | Episodes |
| Chatting | Preferences, conversation history | Working memory |

## Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| No summarization strategy | Context window overflow | Summarize with cheap model at 80% capacity |
| Storing everything | Memory grows unbounded, retrieval degrades | Importance scoring + garbage collection |
| Single memory type | Missing experiential learning or factual recall | Use at least sliding window + semantic |
| No deduplication | Retrieval returns redundant results | Deduplicate at > 0.92 cosine similarity |
| Vector search only | Misses importance and recency signals | Combine similarity with importance and recency |
| No persistence | All memory lost on restart | SQLite minimum, PostgreSQL for production |
