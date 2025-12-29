# Implementation Plan

## Phase 1: The Foundation (Monorepo Setup)
[ ] Step 1: Project Scaffolding

Initialize /frontend (Next.js, Tailwind, Shadcn).

Initialize /backend (FastAPI, Uvicorn).

Create a shared docker-compose.yml (optional) or a simple shell script to run both.

[ ] Step 2: The Communication Bridge

Backend: Create a /chat endpoint using StreamingResponse that sends "Hello World" chunks.

Frontend: Create a basic chat input that consumes the stream using the fetch API and displays it.

[ ] Step 2.1: Error Handling in Streaming Pipeline

Backend: Implement error handling in SSE stream:
- Wrap LLM calls in try-catch, send `event: error` with error details
- Handle tool execution failures (SQL errors, Spark job failures)
- Send structured error events: `{"type": "error", "message": "...", "stage": "..."}`

Frontend: Handle SSE errors gracefully:
- Parse error events from stream
- Display error messages in chat UI with appropriate styling
- Show retry option for recoverable errors
- Log errors for debugging

Sandbox: Wrap react-runner output in Error Boundary:
- Catch runtime errors in generated components
- Display user-friendly error messages
- Show code snippet where error occurred

## Phase 2: The Sandbox (The "Artifact" UI)
[ ] Step 3: Sandbox Component

Install react-runner in the frontend.

Create a Preview component that takes a string of code and renders it inside an Error Boundary.

[ ] Step 3.1: Security Measures for Code Execution

Implement code validation:
- Parse generated code AST to validate imports (only allow Recharts, Shadcn, Lucide)
- Reject code with forbidden patterns (fetch, localStorage, eval, etc.)
- Validate component signature matches contract: `export default function Viz({ data, params })`

Sandbox isolation:
- Wrap react-runner in iframe for additional isolation (optional but recommended)
- Set Content Security Policy headers
- Implement execution timeout (e.g., 5 seconds max render time)

Security utilities:
- Create `/frontend/lib/security/codeValidator.ts` for import/pattern validation
- Add unit tests for security checks

[ ] Step 4: The Parser Utility

Write a utility to extract code blocks from the AI's markdown response (e.g., extracting content between ```tsx blocks).

Connect the Parser to the Preview window so code appears as it streams.

## Phase 3: Data Integration (The "Agent" Logic)
[ ] Step 5: Mock Data Tool

Backend: Implement a Pydantic model for a "Query Result" (columns and rows).

Backend: Create a mock tool get_sales_data() that returns a hardcoded JSON array.

[ ] Step 5.1: Backend Tool Definitions

Define Pydantic models for tools:
- `RunSQLTool`: `query: str`, `limit: int = 1000`, `data_source: Literal["duckdb"]`
- `SubmitSparkTool`: `query: str`, `output_format: Literal["parquet", "csv"] = "parquet"`
- `QueryResult`: `columns: List[str]`, `rows: List[List[Any]]`, `row_count: int`

Implement tool functions:
- `run_sql(query, limit)` - Execute SQL and return JSON array (small subsets)
- `submit_spark(query, format)` - Submit to Spark cluster, return materialized file URL
- Both tools return `QueryResult` or `SparkJobResult` Pydantic models

Register tools with PydanticAI agent:
- Define tool schemas using Pydantic models
- Create tool implementations that call actual data APIs
- Add tool descriptions for LLM to understand when to use each

[ ] Step 6: The System Prompt

Create the "Base System Prompt" in FastAPI that instructs the LLM how to call the data tool and how to write code that uses the data prop.

## Phase 4: Persistence & Polish
[ ] Step 7: Parameterization

Modify the generated UI contract to accept a params object.

Add a sidebar in the UI to allow users to tweak these parameters (e.g., changing colors or date ranges) without re-running SQL.

[ ] Step 7.1: Data Freshness & Metadata

Add data metadata tracking:
- Backend: Include `fetched_at` timestamp in data responses
- Backend: Add `data_version` or `cache_key` to track data changes
- Frontend: Display "Data fetched at: [timestamp]" in UI

Implement data refresh mechanism:
- Add "Refresh Data" button in UI (only visible after initial generation)
- Refresh triggers re-execution of SQL without regenerating UI code
- Show loading state during refresh
- Update data prop while keeping same component code

Cache invalidation strategy:
- Small data (JSON): Cache for 5 minutes, allow manual refresh
- Large data (Parquet): Cache until user explicitly refreshes
- Store cache keys in frontend state for refresh requests

[ ] Step 8: Template Saving

Setup a simple SQLite or Supabase table to save "Templates" (The original prompt + the generated SQL + the generated UI code).

[ ] Step 8.1: Frontend State Management

Design state architecture:
- Chat messages: Array of `{ role: "user" | "assistant", content: string, timestamp }`
- Active artifact: `{ code: string, dataUrl: string | null, params: object }`
- Conversation history: Array of previous artifacts/messages
- Loading states: `{ isGenerating: boolean, isFetchingData: boolean, stage: string }`

Choose state management solution:
- Option A: React Context API (`ChatContext`, `ArtifactContext`)
- Option B: Zustand store (`useChatStore`, `useArtifactStore`)
- Recommendation: Start with Context, migrate to Zustand if complexity grows

Implement state persistence:
- Save conversation history to localStorage (optional: sync to backend)
- Implement "Clear History" functionality
- Handle state restoration on page reload

State structure example:
```typescript
interface ChatState {
  messages: Message[];
  activeArtifact: Artifact | null;
  isGenerating: boolean;
  currentParams: Record<string, any>;
}
```

