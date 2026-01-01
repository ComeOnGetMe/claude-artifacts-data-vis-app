# Architecture: Interactive Data Viz Orchestrator

## 1. High-Level Overview

A full-stack application using **Next.js** for the interactive "Artifact" frontend and **FastAPI** for the heavy-lifting data logic and LLM orchestration.

## 2. Tech Stack

* **Frontend:** Next.js 15, Tailwind CSS, Shadcn UI.
* **Backend:** FastAPI (Python 3.11+).
* **AI Integration:** LangChain or PydanticAI (within FastAPI) for tool-calling.
* **Communication:**
    * **REST:** For standard CRUD and template saving.
    * **SSE (Server-Sent Events):** For streaming AI thoughts and UI code chunks.
* **Data Execution**:  (already provided by external services)
    * **Local DuckDB**: for debugging purposes
    * **Distributed DuckDB:** For immediate SQL execution (all queries return small result sets).

## 3. Agent Workflow & SQL Translation

### Overview: Unified Agent Approach

The agent uses **PydanticAI** with tool-calling capabilities. The SQL translation happens **inside the agent's reasoning process** before it calls data tools. Here's the complete workflow:

### Workflow Steps:

1. **User sends prompt** → Frontend POSTs to `/chat` endpoint with user message

2. **Backend receives & send to LLM agent to analyzes** → PydanticAI agent processes the prompt:
   - Understands user intent (e.g., "Show sales by region")
   - **Translates natural language to SQL** (happens in agent's reasoning)
   - **Infers expected data structure** from the SQL query (column names, types, aggregation patterns)

3. **Agent generates UI code immediately** → Agent generates React/TypeScript code **while** data executes:
   - Analyzes the SQL query structure to predict data shape (columns, types, relationships)
   - Generates React/TypeScript code using Recharts + Shadcn based on expected structure
   - Streams code chunks via SSE as they're generated
   - Code includes placeholder/loading states for when data arrives

4. **Agent calls data tool (parallel or after code generation)** → Agent invokes `run_sql(query, limit)`:
   - Tool receives SQL query string
   - Executes SQL against DuckDB (may happen in parallel with code streaming)
   - Returns `QueryResult` with columns and rows
   - If actual data structure differs significantly, agent may stream code updates

5. **Backend sends SSE to frontend according to agent output**: 
   - backend parses agent output and send different events to frontend accordingly:
   - for output of data tool call, send data as a `data` event
   - for UI code, send as `code` event

6. **Frontend renders progressively** → Frontend receives:
   - UI code chunks (streamed as they're generated)
   - Data payload (streamed directly when query completes)
   - Frontend infers readiness from event patterns (no backend state tracking)
   - Renders component skeleton when code chunks arrive, updates with data when `data` event arrives

### How SQL Translation Works:

The SQL translation happens **inside the PydanticAI agent** through:

1. **System Prompt**: Instructs the LLM about:
   - Available database schemas/tables (provided as context)
   - SQL syntax and best practices
   - How to interpret user requests and translate to SQL
   - **Generate UI code immediately** based on expected data structure from SQL query
   
   Example system prompt excerpt:

   ```text
   You are a data analyst assistant. When users ask questions about data:
   1. Analyze their request and determine what SQL query is needed
   2. Use run_sql() for executing queries (fast, immediate results)
   3. Always include appropriate WHERE clauses and LIMITs
   4. **Generate UI code immediately** after determining the SQL query, based on the expected
      data structure (column names, types, aggregation patterns). Do not wait for query execution.
      Include loading/placeholder states in the generated component.
   
   Available tables: sales (region, amount, date), products (id, name, category)
   ```


2. **Tool Schema**: The `RunSQLTool` Pydantic model defines:

   ```python
   class RunSQLTool(BaseModel):
       query: str  # Agent must provide SQL here
       limit: int = 1000
       data_source: Literal["duckdb"] = "duckdb"
   ```

3. **Agent Reasoning**: When agent decides to call `run_sql`, it must:
   - Generate the SQL query string (LLM translates natural language → SQL)
   - Pass it as the `query` parameter
   - The LLM does this translation as part of its tool-calling decision

   The PydanticAI framework ensures the agent provides a valid SQL string before the tool executes.

### Example Workflow:

**User Prompt:** "Show me sales by region for Q1 2024"

**Agent Processing:**

```text
1. [thought] "User wants sales data grouped by region for Q1 2024"
2. [thought] "I need to query a sales table. This seems like a small query, I'll use run_sql"
3. [thought] "The SQL will return: region (string) and total_sales (number). 
              I'll create a bar chart using Recharts. I'll generate the UI code now."
4. [code] Streams React component code with BarChart (includes loading state)...
5. [tool_call] run_sql(
     query="SELECT region, SUM(amount) as total_sales 
            FROM sales 
            WHERE date >= '2024-01-01' AND date < '2024-04-01' 
            GROUP BY region 
            ORDER BY total_sales DESC",
     limit=1000
   )
6. [tool_result] QueryResult(columns=['region', 'total_sales'], rows=[...])
7. [data] Streams data payload directly: {"type": "data", "payload": {"columns": [...], "rows": [...]}}
8. [stream closes] Backend finishes - frontend infers code completion from event pattern
```

**Key Points:** 
- The SQL translation (step 5) happens **inside the agent** when it decides to call the `run_sql` tool.
- **UI code generation (step 4) happens immediately** after the agent determines the SQL query structure, before data execution.
- The agent infers the expected data structure from the SQL query itself (SELECT columns, aggregations, etc.).
- Data execution may happen in parallel with code streaming, or after code generation completes.
- **Backend is stateless**: It streams events as they occur, frontend infers completion from event patterns (no status events needed).

## 4. System Components

### A. FastAPI Orchestrator (`/backend`)

* **Agent Logic:** Uses PydanticAI to define "Tools" (e.g., `run_sql`).
* **Stateless Streaming:** Processes LLM output and tool results, streams events as they occur.
* **No State Tracking:** Backend doesn't track completion status - just processes and streams events.
* **Data Proxy:** Acts as a secure gateway to your SQL clusters.

### B. Next.js Frontend (`/frontend`)

* **Artifact Processor:** Uses `fetch` with a `ReadableStream` to consume FastAPI's SSE stream.
* **Dynamic Renderer:** `react-runner` to mount the code generated by the Python backend.

## 5. Directory Structure

```text
├── frontend/             # Next.js App
│   ├── components/       # Chat and Preview Sandbox
│   └── lib/              # API clients for FastAPI
├── backend/              # FastAPI App
│   ├── api/              # Routes (chat, data, templates)
│   ├── agents/           # LLM logic & PydanticAI tools
│   ├── core/             # SQL connection logic
│   └── main.py           # Entry point
├── docs/                 # Architecture & Requirements
└── .cursor/rules/        # Agent instructions
```

## 6. SSE Streaming Format Specification

The `/chat` endpoint streams structured events using Server-Sent Events. Each event follows this format:

```
event: <event_type>
data: <json_payload>
```

### Event Types:

**`thought`** - LLM reasoning/thinking process

```json
{
  "type": "thinking",
  "content": "Analyzing your request..."
}
```

**`code`** - UI code chunks (streamed incrementally)

```json
{
  "type": "code_chunk",
  "language": "tsx",
  "content": "import React from 'react';..."
}
```

**`data`** - Data returned by query engine (streamed directly)

```json
{
  "type": "data",
  "payload": {
    "columns": ["region", "total_sales"],
    "rows": [["North", 1000], ["South", 2000]],
    "row_count": 2
  }
}
```

**`error`** - Error occurred during processing

```json
{
  "type": "error",
  "message": "SQL execution failed",
  "stage": "sql_execution" | "code_generation" | "data_fetch"
}
```

**Note on Event Completion:**
- The backend is **stateless** - it simply streams events as they occur from LLM output and tool results
- **Data readiness**: Signaled by the arrival of the `data` event itself
- **Code completion**: Frontend infers from event patterns:
  - When `code` events stop and a different event type arrives (e.g., `data`, `thought`)
  - When the stream closes (all events have been sent)
  - Frontend can render progressively as code chunks arrive, updating when data becomes available
- No backend state tracking needed - backend just processes and streams events

## 7. Frontend-Controlled Rendering Readiness

### Rendering Control:

The frontend controls when to render components by tracking readiness independently. The backend streams events asynchronously, and the frontend decides when both code and data are ready.

### State Tracking (Frontend-Only):

The frontend tracks readiness by observing event patterns - no backend state required:

- **Code State:** 
  - Accumulate code chunks from `code` events
  - Infer `codeComplete: true` when:
    - Code events stop and a different event type arrives (e.g., `data` event)
    - Stream closes (all events sent)
    - Or use a timeout heuristic (e.g., no code events for 500ms)
- **Data State:** 
  - Store data payload from `data` event
  - Set `dataReady: true` immediately when `data` event arrives
- **Rendering Logic:**
  - If `hasCodeChunks && !dataReady`: Render component with loading/placeholder state
  - If `hasCodeChunks && dataReady`: Render component with actual data
  - If `!hasCodeChunks && dataReady`: Store data, wait for code (or render as table fallback)

### Benefits:

- **Stateless backend**: Backend doesn't track completion state - just processes and streams events
- **Progressive rendering**: Show UI skeleton immediately when code chunks arrive
- **Handles race conditions**: Code and data can arrive in any order
- **Better UX**: Users see progress as components become ready
- **Simpler architecture**: Frontend orchestrates everything based on event observation

## 8. Parameterization Timing & Behavior

### States:

- **During Streaming:** Parameter controls are disabled, show "Generating..." indicator
- **After Completion:** Parameter controls are enabled, allow real-time UI updates
- **Re-rendering:** When parameters change, re-render the component with new `params` prop **without** re-querying data

### Implementation:

- Debounce parameter changes (300ms) to avoid excessive re-renders
- Maintain separate state for: `isGenerating`, `generatedCode`, `currentParams`, `data`
- Track readiness independently: `codeComplete`, `dataReady`
- Frontend controls when to render based on readiness state
- Parameter changes trigger component re-mount with updated `params` prop only

## 9. Template Format Schema

Templates are stored as JSON objects with the following structure:

```json
{
  "id": "uuid-v4",
  "prompt": "Show sales by region",
  "generated_sql": "SELECT region, SUM(sales) FROM ...",
  "ui_code": "export default function Viz({ data, params }) {...}",
  "parameters": {
    "title": "Sales by Region",
    "chart_type": "bar",
    "color_scheme": "default"
  },
  "data_source": "duckdb",
  "data": {
    "columns": ["region", "total_sales"],
    "rows": [["North", 1000], ["South", 2000]],
    "row_count": 2
  },
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

**Storage:** Backend persists templates in Postgres. Frontend can load templates via REST API.

## 10. Type Safety & Schema Alignment

### Backend (Pydantic):

- All API responses use Pydantic v2 models
- Tool definitions (run_sql) use Pydantic BaseModel
- Query results typed as `QueryResult` model with `columns: List[str]` and `rows: List[List[Any]]`

### Frontend (TypeScript/Zod):

- Generate TypeScript types from Pydantic models using `pydantic-to-typescript` or manual type definitions
- Validate incoming data with Zod schemas before passing to Sandbox
- Shared type definitions in `/frontend/lib/types.ts`

### Type Generation Strategy:

1. Define Pydantic models in `/backend/models/`
2. Export JSON schemas: `model.model_json_schema()`
3. Generate TypeScript interfaces from schemas (or manually maintain)
4. Create corresponding Zod schemas for runtime validation

## 11. Development Standards

Modular UI: Generated code must be a default export: `export default function Viz({ data, params }) { ... }`.

Data Safety: All data results must be typed via Zod before being passed to the Sandbox.

Templates: Conversation state (Prompt + Generated Code + Params) is stored as a JSON object for sharing.
