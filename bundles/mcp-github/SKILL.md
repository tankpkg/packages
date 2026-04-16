---
name: "@tank/mcp-github"
description: |
  Wire the GitHub MCP server into any AI agent harness. Provides
  github repository management, issues, prs, and code search. Thin wiring package -- does not contain the MCP server
  itself, just the configuration to register it with the agent runtime.

  Trigger phrases: "github", "repository", "pull request", "issues", "code search"
---

# GitHub MCP Tool

Registers the GitHub MCP server with the agent runtime.

## Quick Start

1. Install: `tank install @tank/mcp-github`
2. Set required environment variables (see below)
3. Restart your agent session

## Required Environment Variables

- `GITHUB_PERSONAL_ACCESS_TOKEN`: Required. Set in your environment or `.env`.

## Server Details

| Field | Value |
|-------|-------|
| Command | `npx` |
| Arguments | `-y @modelcontextprotocol/server-github` |
| Transport | STDIO |
| Package | `@modelcontextprotocol/server-github` |

## What This Provides

The GitHub server exposes tools for github repository management, issues, prs, and code search.
Load this package to give your agent access to GitHub capabilities
without manually configuring MCP server settings in each harness.
