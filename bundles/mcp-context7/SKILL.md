---
name: "@tank/mcp-context7"
description: |
  Wire the Context7 MCP server into any AI agent harness. Provides
  up-to-date library documentation and code examples. Thin wiring package -- does not contain the MCP server
  itself, just the configuration to register it with the agent runtime.

  Trigger phrases: "context7", "documentation", "library docs", "code examples", "API reference"
---

# Context7 MCP Tool

Registers the Context7 MCP server with the agent runtime.

## Quick Start

1. Install: `tank install @tank/mcp-context7`
2. No configuration needed -- works out of the box
3. Restart your agent session

## Server Details

| Field | Value |
|-------|-------|
| Command | `npx` |
| Arguments | `-y @upstash/context7-mcp@latest` |
| Transport | STDIO |
| Package | `@upstash/context7-mcp@latest` |

## What This Provides

The Context7 server exposes tools for up-to-date library documentation and code examples.
Load this package to give your agent access to Context7 capabilities
without manually configuring MCP server settings in each harness.
