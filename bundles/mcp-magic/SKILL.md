---
name: "@tank/mcp-magic"
description: |
  Wire the Magic UI MCP server into any AI agent harness. Provides
  magic ui design component generation and prototyping. Thin wiring package -- does not contain the MCP server
  itself, just the configuration to register it with the agent runtime.

  Trigger phrases: "magic ui", "design", "components", "UI generation", "prototyping"
---

# Magic UI MCP Tool

Registers the Magic UI MCP server with the agent runtime.

## Quick Start

1. Install: `tank install @tank/mcp-magic`
2. No configuration needed -- works out of the box
3. Restart your agent session

## Server Details

| Field | Value |
|-------|-------|
| Command | `npx` |
| Arguments | `-y @magicuidesign/mcp@latest` |
| Transport | STDIO |
| Package | `@magicuidesign/mcp@latest` |

## What This Provides

The Magic UI server exposes tools for magic ui design component generation and prototyping.
Load this package to give your agent access to Magic UI capabilities
without manually configuring MCP server settings in each harness.
