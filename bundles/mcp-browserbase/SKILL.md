---
name: "@tank/mcp-browserbase"
description: |
  Wire the Browserbase MCP server into any AI agent harness. Provides
  cloud browser sessions for web scraping and automation. Thin wiring package -- does not contain the MCP server
  itself, just the configuration to register it with the agent runtime.

  Trigger phrases: "browserbase", "cloud browser", "headless browser", "web automation"
---

# Browserbase MCP Tool

Registers the Browserbase MCP server with the agent runtime.

## Quick Start

1. Install: `tank install @tank/mcp-browserbase`
2. Set required environment variables (see below)
3. Restart your agent session

## Required Environment Variables

- `BROWSERBASE_API_KEY`: Required. Set in your environment or `.env`.

## Server Details

| Field | Value |
|-------|-------|
| Command | `npx` |
| Arguments | `-y @browserbasehq/mcp-server-browserbase` |
| Transport | STDIO |
| Package | `@browserbasehq/mcp-server-browserbase` |

## What This Provides

The Browserbase server exposes tools for cloud browser sessions for web scraping and automation.
Load this package to give your agent access to Browserbase capabilities
without manually configuring MCP server settings in each harness.
