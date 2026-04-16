---
name: "@tank/mcp-firecrawl"
description: |
  Wire the Firecrawl MCP server into any AI agent harness. Provides
  web scraping and crawling with structured data extraction. Thin wiring package -- does not contain the MCP server
  itself, just the configuration to register it with the agent runtime.

  Trigger phrases: "firecrawl", "web scraping", "crawling", "data extraction", "scrape"
---

# Firecrawl MCP Tool

Registers the Firecrawl MCP server with the agent runtime.

## Quick Start

1. Install: `tank install @tank/mcp-firecrawl`
2. Set required environment variables (see below)
3. Restart your agent session

## Required Environment Variables

- `FIRECRAWL_API_KEY`: Required. Set in your environment or `.env`.

## Server Details

| Field | Value |
|-------|-------|
| Command | `npx` |
| Arguments | `-y firecrawl-mcp` |
| Transport | STDIO |
| Package | `firecrawl-mcp` |

## What This Provides

The Firecrawl server exposes tools for web scraping and crawling with structured data extraction.
Load this package to give your agent access to Firecrawl capabilities
without manually configuring MCP server settings in each harness.
