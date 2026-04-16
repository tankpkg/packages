---
name: "@tank/mcp-exa-web-search"
description: |
  Wire the Exa Web Search MCP server into any AI agent harness. Provides
  ai-powered web search with semantic understanding. Thin wiring package -- does not contain the MCP server
  itself, just the configuration to register it with the agent runtime.

  Trigger phrases: "exa", "web search", "semantic search", "internet search"
---

# Exa Web Search MCP Tool

Registers the Exa Web Search MCP server with the agent runtime.

## Quick Start

1. Install: `tank install @tank/mcp-exa-web-search`
2. Set required environment variables (see below)
3. Restart your agent session

## Required Environment Variables

- `EXA_API_KEY`: Required. Set in your environment or `.env`.

## Server Details

| Field | Value |
|-------|-------|
| Command | `npx` |
| Arguments | `-y exa-mcp-server` |
| Transport | STDIO |
| Package | `exa-mcp-server` |

## What This Provides

The Exa Web Search server exposes tools for ai-powered web search with semantic understanding.
Load this package to give your agent access to Exa Web Search capabilities
without manually configuring MCP server settings in each harness.
