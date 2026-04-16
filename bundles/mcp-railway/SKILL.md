---
name: "@tank/mcp-railway"
description: |
  Wire the Railway MCP server into any AI agent harness. Provides
  railway.app deployment and infrastructure management. Thin wiring package -- does not contain the MCP server
  itself, just the configuration to register it with the agent runtime.

  Trigger phrases: "railway", "deployment", "infrastructure", "hosting", "railway deploy"
---

# Railway MCP Tool

Registers the Railway MCP server with the agent runtime.

## Quick Start

1. Install: `tank install @tank/mcp-railway`
2. No configuration needed -- works out of the box
3. Restart your agent session

## Server Details

| Field | Value |
|-------|-------|
| Command | `npx` |
| Arguments | `-y @railway/mcp-server` |
| Transport | STDIO |
| Package | `@railway/mcp-server` |

## What This Provides

The Railway server exposes tools for railway.app deployment and infrastructure management.
Load this package to give your agent access to Railway capabilities
without manually configuring MCP server settings in each harness.
