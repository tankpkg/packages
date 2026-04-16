---
name: "@tank/mcp-fal-ai"
description: |
  Wire the fal.ai MCP server into any AI agent harness. Provides
  ai model inference including image generation, video, and audio. Thin wiring package -- does not contain the MCP server
  itself, just the configuration to register it with the agent runtime.

  Trigger phrases: "fal.ai", "image generation", "AI inference", "stable diffusion", "AI models"
---

# fal.ai MCP Tool

Registers the fal.ai MCP server with the agent runtime.

## Quick Start

1. Install: `tank install @tank/mcp-fal-ai`
2. Set required environment variables (see below)
3. Restart your agent session

## Required Environment Variables

- `FAL_KEY`: Required. Set in your environment or `.env`.

## Server Details

| Field | Value |
|-------|-------|
| Command | `npx` |
| Arguments | `-y fal-ai-mcp-server` |
| Transport | STDIO |
| Package | `fal-ai-mcp-server` |

## What This Provides

The fal.ai server exposes tools for ai model inference including image generation, video, and audio.
Load this package to give your agent access to fal.ai capabilities
without manually configuring MCP server settings in each harness.
