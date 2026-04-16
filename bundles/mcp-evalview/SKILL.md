---
name: "@tank/mcp-evalview"
description: |
  Wire the EvalView MCP server into any AI agent harness. Provides
  llm evaluation and output quality assessment. Thin wiring package -- does not contain the MCP server
  itself, just the configuration to register it with the agent runtime.

  Trigger phrases: "evalview", "evaluation", "LLM eval", "quality assessment", "model evaluation"
---

# EvalView MCP Tool

Registers the EvalView MCP server with the agent runtime.

## Quick Start

1. Install: `tank install @tank/mcp-evalview`
2. Set required environment variables (see below)
3. Restart your agent session

## Required Environment Variables

- `OPENAI_API_KEY`: Required. Set in your environment or `.env`.

## Server Details

| Field | Value |
|-------|-------|
| Command | `python3` |
| Arguments | `-m evalview mcp serve` |
| Transport | STDIO |
| Package | `python3` |

## What This Provides

The EvalView server exposes tools for llm evaluation and output quality assessment.
Load this package to give your agent access to EvalView capabilities
without manually configuring MCP server settings in each harness.
