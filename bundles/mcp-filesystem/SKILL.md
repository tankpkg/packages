---
name: "@tank/mcp-filesystem"
description: |
  Wire the Filesystem MCP server into any AI agent harness. Provides
  local filesystem read/write operations for agent file access. Thin wiring package -- does not contain the MCP server
  itself, just the configuration to register it with the agent runtime.

  Trigger phrases: "filesystem", "file access", "read files", "write files", "local files"
---

# Filesystem MCP Tool

Registers the Filesystem MCP server with the agent runtime.

## Quick Start

1. Install: `tank install @tank/mcp-filesystem`
2. No configuration needed -- works out of the box
3. Restart your agent session

## Server Details

| Field | Value |
|-------|-------|
| Command | `npx` |
| Arguments | `-y @modelcontextprotocol/server-filesystem /path/to/your/projects` |
| Transport | STDIO |
| Package | `@modelcontextprotocol/server-filesystem` |

## What This Provides

The Filesystem server exposes tools for local filesystem read/write operations for agent file access.
Load this package to give your agent access to Filesystem capabilities
without manually configuring MCP server settings in each harness.
