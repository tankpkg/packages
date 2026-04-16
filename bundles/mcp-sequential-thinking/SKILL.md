---
name: "@tank/mcp-sequential-thinking"
description: |
  Wire the Sequential Thinking MCP server into any AI agent harness. Provides
  structured step-by-step reasoning and problem decomposition. Thin wiring package -- does not contain the MCP server
  itself, just the configuration to register it with the agent runtime.

  Trigger phrases: "sequential thinking", "reasoning", "problem solving", "step by step"
---

# Sequential Thinking MCP Tool

Registers the Sequential Thinking MCP server with the agent runtime.

## Quick Start

1. Install: `tank install @tank/mcp-sequential-thinking`
2. No configuration needed -- works out of the box
3. Restart your agent session

## Server Details

| Field | Value |
|-------|-------|
| Command | `npx` |
| Arguments | `-y @modelcontextprotocol/server-sequential-thinking` |
| Transport | STDIO |
| Package | `@modelcontextprotocol/server-sequential-thinking` |

## What This Provides

The Sequential Thinking server exposes tools for structured step-by-step reasoning and problem decomposition.
Load this package to give your agent access to Sequential Thinking capabilities
without manually configuring MCP server settings in each harness.
