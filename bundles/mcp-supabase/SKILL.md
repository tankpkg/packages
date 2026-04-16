---
name: "@tank/mcp-supabase"
description: |
  Wire the Supabase MCP server into any AI agent harness. Provides
  supabase database, auth, storage, and edge functions. Thin wiring package -- does not contain the MCP server
  itself, just the configuration to register it with the agent runtime.

  Trigger phrases: "supabase", "database", "postgres", "auth", "storage"
---

# Supabase MCP Tool

Registers the Supabase MCP server with the agent runtime.

## Quick Start

1. Install: `tank install @tank/mcp-supabase`
2. No configuration needed -- works out of the box
3. Restart your agent session

## Server Details

| Field | Value |
|-------|-------|
| Command | `npx` |
| Arguments | `-y @supabase/mcp-server-supabase@latest --project-ref=YOUR_PROJECT_REF` |
| Transport | STDIO |
| Package | `@supabase/mcp-server-supabase@latest` |

## What This Provides

The Supabase server exposes tools for supabase database, auth, storage, and edge functions.
Load this package to give your agent access to Supabase capabilities
without manually configuring MCP server settings in each harness.
