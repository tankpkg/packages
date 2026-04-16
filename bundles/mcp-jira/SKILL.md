---
name: "@tank/mcp-jira"
description: |
  Wire the Jira MCP server into any AI agent harness. Provides
  atlassian jira issue tracking and project management. Thin wiring package -- does not contain the MCP server
  itself, just the configuration to register it with the agent runtime.

  Trigger phrases: "jira", "atlassian", "issue tracking", "project management", "tickets"
---

# Jira MCP Tool

Registers the Jira MCP server with the agent runtime.

## Quick Start

1. Install: `tank install @tank/mcp-jira`
2. Set required environment variables (see below)
3. Restart your agent session

## Required Environment Variables

- `JIRA_URL`: Required. Set in your environment or `.env`.
- `JIRA_EMAIL`: Required. Set in your environment or `.env`.
- `JIRA_API_TOKEN`: Required. Set in your environment or `.env`.

## Server Details

| Field | Value |
|-------|-------|
| Command | `uvx` |
| Arguments | `mcp-atlassian==0.21.0` |
| Transport | STDIO |
| Package | `uvx` |

## What This Provides

The Jira server exposes tools for atlassian jira issue tracking and project management.
Load this package to give your agent access to Jira capabilities
without manually configuring MCP server settings in each harness.
