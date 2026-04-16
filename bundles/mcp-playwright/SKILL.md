---
name: "@tank/mcp-playwright"
description: |
  Wire the Playwright MCP server into any AI agent harness. Provides
  browser automation, testing, and web interaction. Thin wiring package -- does not contain the MCP server
  itself, just the configuration to register it with the agent runtime.

  Trigger phrases: "playwright", "browser automation", "web testing", "browser control", "e2e"
---

# Playwright MCP Tool

Registers the Playwright MCP server with the agent runtime.

## Quick Start

1. Install: `tank install @tank/mcp-playwright`
2. No configuration needed -- works out of the box
3. Restart your agent session

## Server Details

| Field | Value |
|-------|-------|
| Command | `npx` |
| Arguments | `-y @playwright/mcp --browser chrome` |
| Transport | STDIO |
| Package | `@playwright/mcp` |

## What This Provides

The Playwright server exposes tools for browser automation, testing, and web interaction.
Load this package to give your agent access to Playwright capabilities
without manually configuring MCP server settings in each harness.
