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
    * **Distributed DuckDB:** For immediate "Small Subset" SQL execution.
    * **PySpark:** For submitting jobs to remote Spark clusters.

## 3. Agent Workflow & SQL Translation

### Overview: Unified Agent Approach

The agent uses **PydanticAI** with tool-calling capabilities. The SQL translation happens **inside the agent's reasoning process** before it calls data tools. Here's the complete workflow:

### Workflow Steps:

1. **User sends prompt** → Frontend POSTs to `/chat` endpoint with user message

2. **Agent receives & analyzes** → PydanticAI agent processes the prompt:
   - Understands user intent (e.g., "Show sales by region")
   - **Translates natural language to SQL** (happens in agent's reasoning)
   - Decides which tool to call (`run_sql` for small data, `submit_spark` for large)

3. **Agent calls data tool** → Agent invokes `run_sql(query, limit)` or `submit_spark(query)`:
   - Tool receives SQL query string
   - Executes SQL against DuckDB/Spark
   - Returns `QueryResult` with columns and rows

4. **Agent generates UI code** → Agent receives data results:
   - Analyzes data structure (columns, types, sample rows)
   - Generates React/TypeScript code using Recharts + Shadcn
   - Streams code chunks via SSE as they're generated

5. **Frontend renders** → Frontend receives:
   - Data URL or JSON payload
   - Complete UI code
   - Renders component in sandbox with data

### How SQL Translation Works:

The SQL translation happens **inside the PydanticAI agent** through:

1. **System Prompt**: Instructs the LLM about:
   - Available database schemas/tables (provided as context)
   - SQL syntax and best practices
   - When to use `run_sql` vs `submit_spark`
   - How to interpret user requests and translate to SQL
   
   Example system prompt excerpt:

   ```text
   You are a data analyst assistant. When users ask questions about data:
   1. Analyze their request and determine what SQL query is needed
   2. Use run_sql() for queries that return < 1000 rows (fast, immediate results)
   3. Use submit_spark() for large aggregations or full table scans
   4. Always include appropriate WHERE clauses and LIMITs
   
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

### Alternative: Separate Endpoints (For Development/Testing)

For development, you may want separate endpoints:

- `/query-understanding`: Pure SQL translation (no execution)
- `/generate-ui`: Pure UI code generation (no data fetching)

These are useful for:

- Testing individual components
- Debugging SQL generation separately
- Iterative development

**But in production**, the unified `/chat` endpoint with tool-calling is recommended because:

- Agent can adapt based on actual data results
- More efficient (single LLM orchestration)
- Better error handling (agent can retry with corrected SQL)

### Example Workflow:

**User Prompt:** "Show me sales by region for Q1 2024"

**Agent Processing:**

```text
1. [thought] "User wants sales data grouped by region for Q1 2024"
2. [thought] "I need to query a sales table. This seems like a small query, I'll use run_sql"
3. [tool_call] run_sql(
     query="SELECT region, SUM(amount) as total_sales 
            FROM sales 
            WHERE date >= '2024-01-01' AND date < '2024-04-01' 
            GROUP BY region 
            ORDER BY total_sales DESC",
     limit=1000
   )
4. [tool_result] QueryResult(columns=['region', 'total_sales'], rows=[...])
5. [thought] "Data has 2 columns: region (string) and total_sales (number). 
              I'll create a bar chart using Recharts"
6. [code] Streams React component code with BarChart...
```

**Key Point:** The SQL translation (step 3) happens **inside the agent** when it decides to call the `run_sql` tool. The agent's LLM generates the SQL query string as part of its tool-calling decision.

## 4. System Components

### A. FastAPI Orchestrator (`/backend`)

* **Agent Logic:** Uses PydanticAI to define "Tools" (e.g., `run_sql`, `submit_spark`).
* **Artifact Generator:** A specialized endpoint `/generate-ui` that streams back React code blocks.
* **Data Proxy:** Acts as a secure gateway to your Spark/SQL clusters.

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
│   ├── core/             # Spark/SQL connection logic
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

**`data`** - Data ready notification

```json
{
  "type": "data_ready",
  "url": "/api/data/abc123",
  "size": "small" | "large",
  "format": "json" | "parquet"
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

**`done`** - Stream complete

```json
{
  "type": "complete",
  "code_complete": true,
  "data_ready": true
}
```

## 7. Parameterization Timing & Behavior

### States:

- **During Streaming:** Parameter controls are disabled, show "Generating..." indicator
- **After Completion:** Parameter controls are enabled, allow real-time UI updates
- **Re-rendering:** When parameters change, re-render the component with new `params` prop **without** re-querying data

### Implementation:

- Debounce parameter changes (300ms) to avoid excessive re-renders
- Maintain separate state for: `isGenerating`, `generatedCode`, `currentParams`, `dataUrl`
- Parameter changes trigger component re-mount with updated `params` prop only

## 8. Template Format Schema

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
  "data_source": "spark" | "duckdb",
  "data_url": "/api/data/abc123" | null,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

**Storage:** Backend persists templates in Postgres. Frontend can load templates via REST API.

## 9. Type Safety & Schema Alignment

### Backend (Pydantic):

- All API responses use Pydantic v2 models
- Tool definitions (run_sql, submit_spark) use Pydantic BaseModel
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

## 10. Development Standards

Modular UI: Generated code must be a default export: `export default function Viz({ data, params }) { ... }`.

Data Safety: All data results must be typed via Zod before being passed to the Sandbox.

Templates: Conversation state (Prompt + Generated Code + Params) is stored as a JSON object for sharing.
