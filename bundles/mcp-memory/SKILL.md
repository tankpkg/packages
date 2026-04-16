---
name: "@tank/mcp-memory"
description: |
  Wire the Memory MCP server into any AI agent harness. Provides
  persistent memory and knowledge graph for agent context across sessions. Thin wiring package -- does not contain the MCP server
  itself, just the configuration to register it with the agent runtime.

  Trigger phrases: "memory", "knowledge graph", "persistent context", "agent memory"
---

# Memory MCP Tool

Registers the Memory MCP server with the agent runtime.

## Quick Start

1. Install: `tank install @tank/mcp-memory`
2. No configuration needed -- works out of the box
3. Restart your agent session

## Server Details

| Field | Value |
|-------|-------|
| Command | `npx` |
| Arguments | `-y @modelcontextprotocol/server-memory` |
| Transport | STDIO |
| Package | `@modelcontextprotocol/server-memory` |

## What This Provides

The Memory server exposes tools for persistent memory and knowledge graph for agent context across sessions.
Load this package to give your agent access to Memory capabilities
without manually configuring MCP server settings in each harness.
