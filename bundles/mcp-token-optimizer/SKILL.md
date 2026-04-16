---
name: "@tank/mcp-token-optimizer"
description: |
  Wire the Token Optimizer MCP server into any AI agent harness. Provides
  token usage analysis and optimization for llm interactions. Thin wiring package -- does not contain the MCP server
  itself, just the configuration to register it with the agent runtime.

  Trigger phrases: "token optimizer", "token usage", "cost optimization", "LLM tokens"
---

# Token Optimizer MCP Tool

Registers the Token Optimizer MCP server with the agent runtime.

## Quick Start

1. Install: `tank install @tank/mcp-token-optimizer`
2. No configuration needed -- works out of the box
3. Restart your agent session

## Server Details

| Field | Value |
|-------|-------|
| Command | `npx` |
| Arguments | `-y token-optimizer-mcp` |
| Transport | STDIO |
| Package | `token-optimizer-mcp` |

## What This Provides

The Token Optimizer server exposes tools for token usage analysis and optimization for llm interactions.
Load this package to give your agent access to Token Optimizer capabilities
without manually configuring MCP server settings in each harness.
