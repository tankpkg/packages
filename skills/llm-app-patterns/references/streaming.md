# Streaming

Sources: Huyen (AI Engineering), Brousseau & Sharp (LLMs in Production), 2025–2026 production patterns from Vercel AI SDK and Anthropic documentation analysis

Covers: streaming transport protocols, server implementation, client consumption, tool call streaming, backpressure, error recovery, UX patterns.

## Why Streaming Matters

Without streaming, users wait for the full LLM response before seeing anything. For a 500-token response at 50 tokens/second, that is a 10-second blank screen. With streaming, the first tokens appear within 200–500ms and users read while the model generates.

The UX impact is decisive:
- Perceived latency drops from full generation time to time-to-first-token
- Users stay engaged because they see progress
- Long responses become readable, not daunting

## Transport Protocol Comparison

| Protocol | Direction | Use Case | Overhead |
|----------|-----------|----------|----------|
| Server-Sent Events (SSE) | Server → Client | LLM streaming, token delivery | Low |
| WebSockets | Bidirectional | Chat with user interruption | Higher |
| HTTP chunked transfer | Server → Client | Simple streaming without reconnect | Low |
| Long polling | Server → Client | Legacy fallback | High |

**Default choice: SSE.** It is HTTP-native, reconnects automatically, and requires no special server infrastructure. Use WebSockets only when the client needs to send messages mid-stream (voice interruption, user cancellation with acknowledgement).

## Server-Sent Events (SSE)

SSE is a unidirectional HTTP connection where the server pushes newline-delimited events. Each event is a `data:` prefixed text line.

### Wire Format

```
data: {"type": "content_delta", "text": "Hello"}

data: {"type": "content_delta", "text": " world"}

data: {"type": "message_stop"}

```

The client EventSource API handles reconnection automatically using the `Last-Event-ID` header.

### Server Implementation Pattern

```
POST /api/chat
    → validate request
    → set headers:
        Content-Type: text/event-stream
        Cache-Control: no-cache
        Connection: keep-alive
    → call LLM SDK with stream=true
    → for each chunk from stream:
        write "data: " + JSON(chunk) + "\n\n"
        flush immediately (disable response buffering)
    → write "data: [DONE]\n\n"
    → close connection
```

**Critical**: Flush after every chunk. Buffered responses defeat the purpose of streaming. Most reverse proxies (nginx, Caddy) buffer by default — configure `X-Accel-Buffering: no` or equivalent.

### Proxy Buffering (Common Production Problem)

| Layer | Problem | Fix |
|-------|---------|-----|
| nginx | Buffers SSE by default | Add `proxy_buffering off;` for streaming routes |
| Cloudflare | Edge caches responses | Set `Cache-Control: no-store` |
| AWS ALB | 60s idle timeout | Configure idle timeout > max generation time |
| Vercel (serverless) | Function timeout | Use edge runtime for streaming routes |

## Client Consumption

### Browser EventSource

The browser's native `EventSource` API handles SSE connections, including automatic reconnection with exponential backoff.

```
function streamLLMResponse(userMessage, onChunk, onDone, onError):
    source = new EventSource("/api/chat?message=" + encode(userMessage))

    source.onmessage = (event) =>
        if event.data == "[DONE]":
            onDone()
            source.close()
            return
        chunk = JSON.parse(event.data)
        onChunk(chunk.text)

    source.onerror = (error) =>
        onError(error)
        source.close()
```

**Limitation**: EventSource only supports GET. For POST requests (common for chat), use `fetch()` with the ReadableStream API instead.

### Fetch-Based Streaming (POST Support)

```
async function streamChat(messages, onChunk, onDone):
    response = await fetch("/api/chat", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({messages}),
    })

    reader = response.body.getReader()
    decoder = new TextDecoder()

    loop:
        {done, value} = await reader.read()
        if done: break
        text = decoder.decode(value, {stream: true})
        for each line in text.split("\n"):
            if line.startswith("data: "):
                payload = line.slice(6)
                if payload == "[DONE]": break loop
                onChunk(JSON.parse(payload).text)

    onDone()
```

## Streaming with Tool Calls

Tool calls interrupt the text stream. The flow becomes:

```
Stream starts
    → content_delta events (text accumulates)
    → tool_call event (model requests tool execution)
    → [stream pauses or continues with other content]
    → client executes tool
    → tool_result sent back to model
    → model continues streaming final response
```

### Event Types to Handle

| Event Type | Action |
|------------|--------|
| `content_delta` | Append text to UI |
| `tool_call_start` | Show "thinking" or tool indicator |
| `tool_call_delta` | Accumulate tool input JSON |
| `tool_call_complete` | Execute tool; show result |
| `message_stop` | Finalize and close stream |
| `error` | Show error; enable retry |

### Parallel Tool Streaming Pattern

```
When multiple tool_calls arrive in one message:
    collect all tool_call_start events until message_delta ends
    execute all tools in parallel (Promise.all / asyncio.gather)
    send all tool_results in a single follow-up message
    open new stream for final response
```

Never execute parallel tool calls sequentially — you lose the latency benefit.

## Backpressure and Buffer Management

Fast models generate tokens faster than slow networks can transmit them. Without backpressure, server memory fills with buffered chunks.

```
# Server-side: check if client is still connected before writing
for each chunk:
    if client.disconnected:
        abort LLM stream
        break
    write chunk
    flush
```

**Abort on disconnect**: Always propagate client disconnection upstream to the LLM API. Unnecessary generation wastes tokens and money.

### Client-Side Token Buffer

Render tokens at a controlled rate (typewriter effect) rather than all at once as they arrive. Store received tokens in a buffer and drain at a fixed rate.

```
token_buffer = []
render_interval = 30ms  # ~33 tokens/sec — fast but readable

onChunk(text):
    token_buffer.push(text)

render_loop (every render_interval):
    if token_buffer.empty: return
    batch = token_buffer.splice(0, 3)  # drain 3 tokens per frame
    append_to_display(batch.join(""))
```

## Error Handling and Reconnection

| Error | Client Behavior | Server Behavior |
|-------|-----------------|-----------------|
| Network dropped mid-stream | Reconnect with Last-Event-ID | Resume from last sent event ID |
| LLM API rate limit | Retry after delay; show indicator | Log 429, surface wait time to client |
| LLM API timeout | Close stream; show partial + retry option | Set server-side timeout; return partial |
| Invalid JSON chunk | Skip chunk; log; continue | Ensure chunks are always valid JSON |
| Max token limit hit | Treat message_stop as normal end | Send finish_reason: "length" in stop event |

### Partial Response Recovery

When a stream breaks mid-response, preserve what was received:

```
on stream error:
    save partial_text = accumulated text so far
    show: partial_text + "[Response interrupted — retry?]"
    offer retry button that resumes from partial context
```

## UX Patterns

### Loading State Sequence

| Phase | Display |
|-------|---------|
| Request sent, no tokens yet | Blinking cursor or "Thinking…" indicator |
| First token received | Remove indicator; begin rendering text |
| Tool call in progress | Show tool name and input (optional) |
| Stream complete | Remove cursor; enable copy/share actions |

### When Not to Stream

| Situation | Prefer Non-Streaming |
|-----------|---------------------|
| Response is short (< 50 tokens) | Streaming overhead not worth it |
| Downstream pipeline needs complete response | Parse after full generation |
| Background processing (no UI) | Async batch; stream adds no value |
| Response will be cached | Cache complete response |

### Streaming with Reasoning Models

Extended thinking models (o1, Claude extended thinking) may produce long reasoning traces before the final answer. Options:

- Stream reasoning tokens to a separate "thinking" panel (show progress)
- Suppress reasoning tokens from the user; stream only the answer
- Show a "reasoning in progress" indicator; stream the answer when ready

## Implementation Checklist

- [ ] Response headers include `Content-Type: text/event-stream` and `Cache-Control: no-cache`
- [ ] Proxy buffering disabled for streaming routes
- [ ] Chunks flushed immediately, not batched
- [ ] Client handles `[DONE]` sentinel and closes connection
- [ ] LLM stream aborted when client disconnects
- [ ] Tool calls accumulated before execution; executed in parallel
- [ ] Partial response preserved on stream error
- [ ] Rate limit and timeout errors surface to user with retry option
- [ ] Serverless functions using edge runtime (not standard) for streaming
