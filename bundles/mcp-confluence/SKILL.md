---
name: "@tank/mcp-confluence"
description: |
  Wire the Confluence MCP server into any AI agent harness. Provides
  atlassian confluence wiki and documentation management. Thin wiring package -- does not contain the MCP server
  itself, just the configuration to register it with the agent runtime.

  Trigger phrases: "confluence", "atlassian", "wiki", "documentation", "knowledge base"
---

# Confluence MCP Tool

Registers the Confluence MCP server with the agent runtime.

## Quick Start

1. Install: `tank install @tank/mcp-confluence`
2. Set required environment variables (see below)
3. Restart your agent session

## Required Environment Variables

- `CONFLUENCE_BASE_URL`: Required. Set in your environment or `.env`.
- `CONFLUENCE_EMAIL`: Required. Set in your environment or `.env`.
- `CONFLUENCE_API_TOKEN`: Required. Set in your environment or `.env`.

## Server Details

| Field | Value |
|-------|-------|
| Command | `npx` |
| Arguments | `-y confluence-mcp-server` |
| Transport | STDIO |
| Package | `confluence-mcp-server` |

## What This Provides

The Confluence server exposes tools for atlassian confluence wiki and documentation management.
Load this package to give your agent access to Confluence capabilities
without manually configuring MCP server settings in each harness.
