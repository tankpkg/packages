# Agent Frameworks

Sources: LangGraph (Documentation, 2025), CrewAI (Documentation, 2025), Mastra (Documentation, 2025), OpenAI (Agents SDK, 2025), Microsoft (Semantic Kernel, 2025), AutoGen/AG2 (Documentation, 2024), Anthropic (Tool Use Guide, 2025)

Covers: framework comparison, selection criteria, LangGraph state graphs, CrewAI crews, Mastra agents and workflows, OpenAI Agents SDK, Semantic Kernel, and migration patterns between frameworks.

## Framework Landscape (2025-2026)

| Framework | Language | Stars | Key Strength | Best For |
|-----------|----------|-------|-------------|----------|
| LangGraph | Python, TypeScript | 28K+ | State graphs, fine-grained control | Complex workflows, custom architectures |
| CrewAI | Python | 25K+ | Role-based crews, rapid prototyping | Multi-agent teams, structured processes |
| Mastra | TypeScript | 22K+ | TS-native, workflow engine, integrations | TypeScript projects, workflow automation |
| AutoGen/AG2 | Python, C#, Java | 56K+ | Multi-language, distributed runtime | Enterprise, polyglot environments |
| Semantic Kernel | C#, Python, Java | 22K+ | Enterprise integration, plugin system | .NET/Java enterprise, Microsoft stack |
| OpenAI Agents SDK | Python | 15K+ | Native OpenAI integration, simple API | OpenAI-only projects, rapid prototyping |

## Framework Selection Decision Tree

```
What is your primary language?
  TypeScript → Mastra (native TS) or LangGraph (TS port)
  Python → LangGraph or CrewAI
  C# / Java → Semantic Kernel or AutoGen
  Multiple → AutoGen (polyglot support)

What level of control do you need?
  Maximum (custom state machines, complex routing) → LangGraph
  Role-based teams (structured collaboration) → CrewAI
  Workflow-first (steps, conditions, branching) → Mastra
  Simple tool calling → OpenAI Agents SDK or Anthropic direct

Are you vendor-locked?
  OpenAI only → OpenAI Agents SDK
  Anthropic only → Direct tool use (no framework needed)
  Multi-vendor → LangGraph, CrewAI, or Mastra
  Microsoft ecosystem → Semantic Kernel
```

## LangGraph

Graph-based agent orchestration. Define agents as nodes, transitions as edges, and state flows through the graph. Maximum control over execution flow.

### Core Concepts

| Concept | Description |
|---------|-------------|
| StateGraph | Graph definition with typed state |
| Nodes | Functions that read and write state |
| Edges | Transitions between nodes (static or conditional) |
| Checkpointer | Persistence layer for state (enables interrupt/resume) |
| State | TypedDict/Pydantic flowing through the graph |

### Basic Agent Graph (Python)

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    next_action: str

def agent_node(state: AgentState) -> dict:
    """LLM reasons about current state and decides action."""
    response = llm.invoke(state["messages"])
    return {"messages": [response]}

def tool_node(state: AgentState) -> dict:
    """Execute tool calls from the last message."""
    last_message = state["messages"][-1]
    results = execute_tools(last_message.tool_calls)
    return {"messages": results}

def should_continue(state: AgentState) -> str:
    """Route based on whether the agent wants to use a tool."""
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return "end"

# Build graph
graph = StateGraph(AgentState)
graph.add_node("agent", agent_node)
graph.add_node("tools", tool_node)
graph.set_entry_point("agent")
graph.add_conditional_edges("agent", should_continue, {
    "tools": "tools",
    "end": END
})
graph.add_edge("tools", "agent")  # After tools, back to agent

app = graph.compile()
```

### LangGraph TypeScript

```typescript
import { StateGraph, END } from "@langchain/langgraph";
import { BaseMessage } from "@langchain/core/messages";

interface AgentState {
  messages: BaseMessage[];
}

const graph = new StateGraph<AgentState>({
  channels: {
    messages: { reducer: (a, b) => [...a, ...b], default: () => [] },
  },
});

graph.addNode("agent", agentNode);
graph.addNode("tools", toolNode);
graph.setEntryPoint("agent");
graph.addConditionalEdges("agent", shouldContinue, {
  tools: "tools",
  end: END,
});
graph.addEdge("tools", "agent");

const app = graph.compile();
```

### LangGraph Strengths

- Fine-grained control over execution flow
- Built-in checkpointing (interrupt/resume)
- Human-in-the-loop via interrupt_before/interrupt_after
- Streaming support for partial results
- Durable execution (survives process restarts)
- Both Python and TypeScript SDKs

### LangGraph Weaknesses

- Steeper learning curve than alternatives
- Graph definition verbose for simple agents
- LangChain ecosystem dependency (can be heavy)

## CrewAI

Role-based multi-agent orchestration. Define agents with roles, goals, and backstories; assign them tasks; run as a crew.

### Core Concepts

| Concept | Description |
|---------|-------------|
| Agent | An entity with role, goal, backstory, tools, and LLM |
| Task | A unit of work assigned to an agent |
| Crew | A team of agents executing tasks together |
| Process | Execution strategy: sequential or hierarchical |

### Basic Crew (Python)

```python
from crewai import Agent, Task, Crew, Process

researcher = Agent(
    role="Senior Research Analyst",
    goal="Find comprehensive, accurate information on the topic",
    backstory="You are an expert researcher with 20 years of experience...",
    tools=[search_tool, scraper_tool],
    llm="gpt-4o",
    verbose=True
)

writer = Agent(
    role="Technical Writer",
    goal="Create clear, engaging technical content",
    backstory="Award-winning technical writer specializing in...",
    tools=[],
    llm="claude-sonnet-4-20250514"
)

research_task = Task(
    description="Research {topic} thoroughly. Find key facts, statistics, examples.",
    agent=researcher,
    expected_output="Detailed research report with citations"
)

writing_task = Task(
    description="Write a comprehensive article based on the research.",
    agent=writer,
    expected_output="2000-word article in markdown",
    context=[research_task]  # Receives research output as context
)

crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, writing_task],
    process=Process.sequential,
    memory=True,
    verbose=True
)

result = crew.kickoff(inputs={"topic": "AI agent architectures"})
```

### CrewAI Strengths

- Intuitive role-based abstraction
- Built-in memory system (short-term, long-term, entity, external)
- Rapid prototyping — define crews in minutes
- Visual crew editor (CrewAI Studio)
- 450M+ workflows/month in production

### CrewAI Weaknesses

- Less fine-grained control than LangGraph
- Python-only
- Abstraction can hide important execution details
- Harder to implement custom routing logic

## Mastra

TypeScript-native agent framework with built-in workflow engine, tool system, and integrations.

### Core Concepts

| Concept | Description |
|---------|-------------|
| Agent | TypeScript class with tools, model, and instructions |
| Tool | Typed function with Zod schema validation |
| Workflow | Step-based execution engine with conditions and branching |
| Integration | Pre-built connectors to external services |

### Basic Agent (TypeScript)

```typescript
import { Agent } from "@mastra/core/agent";
import { openai } from "@ai-sdk/openai";
import { z } from "zod";
import { createTool } from "@mastra/core/tools";

const searchTool = createTool({
  id: "web-search",
  description: "Search the web for information",
  inputSchema: z.object({
    query: z.string().describe("Search query"),
  }),
  execute: async ({ context }) => {
    const results = await searchAPI(context.query);
    return { results };
  },
});

const researchAgent = new Agent({
  name: "Research Agent",
  instructions: "You are a helpful research assistant...",
  model: openai("gpt-4o"),
  tools: { "web-search": searchTool },
});

const response = await researchAgent.generate("What are the latest AI trends?");
```

### Mastra Workflow Engine

```typescript
import { Workflow } from "@mastra/core/workflows";

const researchWorkflow = new Workflow({
  name: "research-pipeline",
  steps: [
    {
      id: "search",
      execute: async (context) => {
        return await searchAgent.generate(context.query);
      },
    },
    {
      id: "analyze",
      execute: async (context) => {
        return await analysisAgent.generate(context.searchResults);
      },
    },
    {
      id: "review",
      when: { "analyze.confidence": { $lt: 0.8 } },
      execute: async (context) => {
        return await reviewAgent.generate(context.analysis);
      },
    },
  ],
});
```

### Mastra Strengths

- TypeScript-native with full type safety
- Zod-based tool schemas (validated at compile time)
- Built-in workflow engine with conditions and branching
- Integrations ecosystem (GitHub, Slack, databases)
- Built-in observability and tracing

### Mastra Weaknesses

- TypeScript only (no Python)
- Newer framework, smaller community
- Fewer production case studies than LangGraph/CrewAI

## OpenAI Agents SDK

Lightweight SDK for building agents with OpenAI models. Focused on simplicity and native OpenAI integration.

### Basic Agent

```python
from openai import OpenAI
from agents import Agent, Runner

agent = Agent(
    name="Research Assistant",
    instructions="You are a helpful research assistant...",
    model="gpt-4o",
    tools=[search_tool, calculator_tool],
)

result = Runner.run_sync(agent, "What is the GDP of France?")
print(result.final_output)
```

### Strengths and Limitations

| Strength | Limitation |
|----------|-----------|
| Simple API, quick start | OpenAI models only |
| Native function calling | Limited orchestration patterns |
| Hosted infrastructure option | Less community tooling |
| Built-in tracing | No state graph abstraction |

## Semantic Kernel

Microsoft's enterprise agent framework. Plugin-based architecture with strong .NET and enterprise integration.

### Key Differentiators

| Feature | Description |
|---------|-------------|
| Plugin system | Modular tool packages that can be shared |
| Planners | Built-in Handlebars and Stepwise planners |
| Memory connectors | Azure AI Search, Qdrant, Chroma, Pinecone |
| Enterprise auth | Azure AD, managed identity integration |
| Multi-language | C#, Python, Java SDKs |

### When to Choose Semantic Kernel

- .NET or Java enterprise applications
- Azure-heavy infrastructure
- Need for enterprise governance and compliance
- Plugin marketplace matters for your use case

## Framework Migration Patterns

### CrewAI to LangGraph

| CrewAI Concept | LangGraph Equivalent |
|----------------|---------------------|
| Agent | Node function |
| Task | Node + edge configuration |
| Crew (sequential) | Linear graph edges |
| Crew (hierarchical) | Conditional edges with supervisor node |
| Memory | Checkpointer + custom state |

### Migration Strategy

1. Map each CrewAI agent to a LangGraph node function
2. Map task dependencies to graph edges
3. Replace crew process with graph topology
4. Add checkpointing for state persistence
5. Implement custom routing via conditional edges

### LangGraph to Mastra

| LangGraph Concept | Mastra Equivalent |
|-------------------|-------------------|
| StateGraph | Workflow |
| Node | Workflow step |
| Conditional edge | Step `when` condition |
| Checkpointer | Built-in workflow persistence |
| Tool node | Tool with Zod schema |

## Framework Comparison Matrix

| Feature | LangGraph | CrewAI | Mastra | OpenAI SDK | Semantic Kernel |
|---------|-----------|--------|--------|------------|----------------|
| Language | Python, TS | Python | TypeScript | Python | C#, Python, Java |
| Control level | Maximum | Medium | High | Low | Medium |
| Learning curve | Steep | Gentle | Moderate | Easy | Moderate |
| Multi-agent | Yes (graphs) | Yes (crews) | Yes (workflows) | Basic | Yes (plugins) |
| HITL | Built-in | Basic | Workflow suspend | Manual | Manual |
| State management | Graph state | Crew memory | Workflow state | Conversation | Kernel memory |
| Checkpointing | Yes | No | Yes | No | No |
| Streaming | Yes | Limited | Yes | Yes | Yes |
| Vendor lock-in | None | None | None | OpenAI | Microsoft-leaning |
| Production scale | Proven | Proven | Growing | Proven | Proven |

## Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Choosing framework before understanding problem | Over/under-engineering | Map requirements to framework strengths first |
| Using CrewAI for custom routing | Fighting the abstraction | Switch to LangGraph for complex routing |
| Using LangGraph for simple sequential agents | Unnecessary complexity | Use CrewAI or even direct API calls |
| Ignoring TypeScript ecosystem | Missing Mastra benefits for TS projects | Evaluate Mastra for TypeScript-native projects |
| Vendor-locking to one provider | Cannot switch models | Use LangGraph or Mastra (multi-provider support) |
| Skipping state persistence | Cannot resume after failure | Add checkpointing from the start |
