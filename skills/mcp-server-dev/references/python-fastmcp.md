# Python FastMCP 3

Sources: FastMCP 3 documentation (gofastmcp.com, 2026), MCP Python SDK, MCP Specification (2025-06-18)

Covers: FastMCP server creation, decorator-based tools/resources/prompts, Pydantic validation, Context object, lifespan management, server composition, OpenAPI import, dependency injection, middleware, and deployment patterns.

## Installation

```bash
pip install fastmcp
# or with uv:
uv add fastmcp
```

Verify: `fastmcp version`

## Basic Server

```python
from fastmcp import FastMCP

mcp = FastMCP("my-server")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b

if __name__ == "__main__":
    mcp.run()
```

Run locally: `fastmcp run server.py`
Run with MCP Inspector: `fastmcp dev server.py`

FastMCP auto-generates JSON Schema from Python type hints — no manual schema definition needed. Docstrings become tool descriptions.

## Tool Registration

### Decorator Syntax

```python
@mcp.tool()
def search_users(query: str, limit: int = 10) -> list[dict]:
    """Search users by name or email. Returns matching profiles."""
    return db.search(query, limit)
```

### With Pydantic Models

```python
from pydantic import BaseModel, Field

class SearchParams(BaseModel):
    query: str = Field(description="Search term")
    limit: int = Field(default=10, ge=1, le=100)

class UserResult(BaseModel):
    id: str
    name: str
    email: str

@mcp.tool()
def search_users(params: SearchParams) -> list[UserResult]:
    """Search users by name or email."""
    results = db.search(params.query, params.limit)
    return [UserResult(**r) for r in results]
```

Pydantic models provide richer validation — min/max, regex patterns, nested objects — than bare type hints.

### Tool Configuration

```python
@mcp.tool(
    name="search-users",          # Override function name
    description="Search users",    # Override docstring
    annotations={
        "readOnlyHint": True,
        "openWorldHint": False
    }
)
def search(query: str) -> list[dict]:
    ...
```

### Error Handling

Return errors so the LLM can self-correct:

```python
from fastmcp.exceptions import ToolError

@mcp.tool()
def fetch_url(url: str) -> str:
    """Fetch content from a URL."""
    try:
        response = httpx.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except httpx.HTTPError as e:
        raise ToolError(f"HTTP error: {e}")
```

`ToolError` sets `isError: true` in the response — the LLM sees the error and can retry or adjust.

### Async Tools

```python
@mcp.tool()
async def fetch_data(url: str) -> str:
    """Fetch data from an API endpoint."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.text
```

FastMCP supports both sync and async handlers. Prefer async for I/O-bound operations.

## Resource Registration

### Static Resources

```python
@mcp.resource("config://app")
def get_config() -> str:
    """Application configuration."""
    return json.dumps(load_config())
```

### Dynamic Resource Templates

```python
@mcp.resource("users://{user_id}/profile")
def get_user_profile(user_id: str) -> str:
    """User profile data."""
    user = db.get_user(user_id)
    return json.dumps(user)
```

URI parameters are extracted and passed as function arguments.

### Resource with MIME Type

```python
@mcp.resource("docs://readme", mime_type="text/markdown")
def get_readme() -> str:
    """Project README."""
    return Path("README.md").read_text()
```

## Prompt Registration

```python
@mcp.prompt()
def review_code(code: str, language: str = "python") -> str:
    """Code review prompt template."""
    return f"Review this {language} code for best practices:\n\n{code}"
```

For multi-message prompts:

```python
from fastmcp.prompts.base import Message, UserMessage, AssistantMessage

@mcp.prompt()
def debug_error(error: str, stacktrace: str) -> list[Message]:
    """Debug an error with context."""
    return [
        UserMessage(f"I'm seeing this error:\n{error}\n\nStacktrace:\n{stacktrace}"),
        AssistantMessage("Let me analyze the error and stacktrace..."),
        UserMessage("What's the root cause and how do I fix it?")
    ]
```

## Context Object

Access MCP capabilities inside handlers:

```python
from fastmcp import Context

@mcp.tool()
async def process_files(files: list[str], ctx: Context) -> str:
    """Process files with progress reporting."""
    for i, f in enumerate(files):
        await process(f)
        await ctx.report_progress(i + 1, len(files))
        await ctx.info(f"Processed {f}")
    return f"Processed {len(files)} files"
```

### Context Methods

| Method | Purpose |
|--------|---------|
| `ctx.report_progress(current, total)` | Progress notifications |
| `ctx.info(msg)` / `ctx.debug(msg)` / `ctx.error(msg)` | Logging |
| `ctx.read_resource(uri)` | Read a resource from within a tool |
| `ctx.sample(messages, max_tokens)` | Request LLM completion from client |
| `ctx.elicit(message, schema)` | Request user input |
| `ctx.request_context` | Access request metadata |

## Lifespan Management

Initialize and clean up shared resources (DB pools, HTTP clients):

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def app_lifespan(server: FastMCP):
    db = await create_db_pool()
    try:
        yield {"db": db}
    finally:
        await db.close()

mcp = FastMCP("db-server", lifespan=app_lifespan)

@mcp.tool()
async def query(sql: str, ctx: Context) -> str:
    """Execute a SQL query."""
    db = ctx.request_context.lifespan_context["db"]
    result = await db.fetch(sql)
    return json.dumps(result)
```

The lifespan context manager runs once at server startup and teardown — connection pools, caches, and other shared state go here.

## Server Composition

Combine multiple servers into one:

```python
users_mcp = FastMCP("users")
orders_mcp = FastMCP("orders")

# Register tools on each...

main = FastMCP("main")
main.mount("users", users_mcp)
main.mount("orders", orders_mcp)
```

Tools from mounted servers are namespaced: `users/search`, `orders/list`.

## OpenAPI Import

Generate an MCP server from an OpenAPI specification:

```python
from fastmcp import FastMCP

mcp = FastMCP.from_openapi(
    url="https://api.example.com/openapi.json",
    name="example-api"
)
```

Each API endpoint becomes an MCP tool with auto-generated schemas.

## Dependency Injection

Inject request-scoped values (HTTP request, auth tokens, user identity):

```python
from fastmcp import FastMCP
from fastmcp.server.dependencies import get_http_request

mcp = FastMCP("auth-server")

@mcp.tool()
async def get_profile(ctx: Context) -> dict:
    """Get current user profile."""
    request = get_http_request(ctx)
    token = request.headers.get("Authorization", "").removeprefix("Bearer ")
    user = await verify_token(token)
    return {"name": user.name, "email": user.email}
```

## Middleware

Add cross-cutting concerns:

```python
from fastmcp.server.middleware import Middleware

class LoggingMiddleware(Middleware):
    async def handle_tool_call(self, request, call_next):
        print(f"Tool called: {request.params.name}")
        result = await call_next(request)
        print(f"Tool result: {result}")
        return result

mcp = FastMCP("my-server", middleware=[LoggingMiddleware()])
```

Built-in middleware: `RateLimiting`, `Caching`, `ErrorHandling`, `Timing`.

## Running Servers

### Development

```bash
# Run with auto-reload:
fastmcp dev server.py

# Run with MCP Inspector:
fastmcp dev server.py --inspect
```

### stdio (Local)

```bash
# Direct stdio:
python server.py
# or:
fastmcp run server.py
```

### HTTP (Remote)

```bash
# Streamable HTTP:
fastmcp run server.py --transport streamable-http --port 8000

# With uvicorn directly:
uvicorn server:mcp.http_app --host 0.0.0.0 --port 8000
```

### Install into Claude Desktop

```bash
fastmcp install server.py --name "My Server"
```

This generates the Claude Desktop config entry automatically.

## Testing

```python
import pytest
from fastmcp import FastMCP, Client

mcp = FastMCP("test-server")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

@pytest.mark.anyio
async def test_add():
    async with Client(mcp) as client:
        result = await client.call_tool("add", {"a": 2, "b": 3})
        assert result[0].text == "5"

@pytest.mark.anyio
async def test_list_tools():
    async with Client(mcp) as client:
        tools = await client.list_tools()
        assert any(t.name == "add" for t in tools)
```

`Client(mcp)` connects via `InMemoryTransport` — no network, no process spawning.

## FastMCP vs Low-Level Python SDK

| Feature | FastMCP 3 | mcp (low-level) |
|---------|-----------|-----------------|
| Tool definition | `@mcp.tool()` decorator | Manual `Tool` objects |
| Schema generation | Auto from type hints | Manual JSON Schema |
| Validation | Pydantic built-in | Manual |
| Composition | `mount()` | Manual routing |
| Testing | `Client(mcp)` in-memory | Manual transport setup |
| OpenAPI import | `from_openapi()` | Not available |
| Recommended for | Most use cases | Custom protocol handling |

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| No docstring on tool | Add descriptive docstring — it becomes the tool description |
| Missing type hints | Add types — FastMCP generates schemas from them |
| Sync I/O in async server | Use `async` handlers with `httpx.AsyncClient` |
| Large return values | Use resources for large data, return summary in tool |
| No lifespan for DB | Use `lifespan` to manage connection pools |
| Bare `except` in tools | Raise `ToolError` for LLM-visible errors |
