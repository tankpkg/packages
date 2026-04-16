---
name: "@tank/mcp-omega-memory"
description: |
  Wire the Omega Memory MCP server into any AI agent harness. Provides
  advanced persistent memory with semantic search and retrieval. Thin wiring package -- does not contain the MCP server
  itself, just the configuration to register it with the agent runtime.

  Trigger phrases: "omega memory", "semantic memory", "agent memory", "persistent context"
---

# Omega Memory MCP Tool

Registers the Omega Memory MCP server with the agent runtime.

## Quick Start

1. Install: `tank install @tank/mcp-omega-memory`
2. No configuration needed -- works out of the box
3. Restart your agent session

## Server Details

| Field | Value |
|-------|-------|
| Command | `uvx` |
| Arguments | `omega-memory serve` |
| Transport | STDIO |
| Package | `uvx` |

## What This Provides

The Omega Memory server exposes tools for advanced persistent memory with semantic search and retrieval.
Load this package to give your agent access to Omega Memory capabilities
without manually configuring MCP server settings in each harness.
