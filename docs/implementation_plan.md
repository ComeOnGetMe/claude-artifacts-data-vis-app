# Implementation Plan

## Phase 1: The Foundation (Monorepo Setup)

[x] Step 1: Project Scaffolding

Initialize /frontend (Next.js, Tailwind, Shadcn).

Initialize /backend (FastAPI, Uvicorn, Postgres).

Create a shared docker-compose.yml to run frontend, backend, DB containers.

[x] Step 2: The Communication Bridge

Backend:

- Create a /chat endpoint using StreamingResponse that sends "Hello World" chunks.
  - Create a test that sends arbitrary text input and verify the response
- Create a /query/local_duckdb endpoint using a local duckdb worker (python subprocess) for debugging
  - Implement a Pydantic model for a "Query Result" (columns and rows)
  - Create a test that send a trivial SQL and verify response

Frontend:

- Create a basic chat input that consumes the stream using the fetch API and displays it.
  - Create a handler for text events and displays it
  - Create tests for starting and continuing a multi-turn conversation

[x] Step 2.1: The UI components

- Create a handler for `data` event that parses and displays data in a table
- Create a handler for `code` event that parses tsx code and acknowledge on frontend
- Create a word-matching rule in backend to trigger data and code events to test above
<!-- - Create a handler for `code` event that accumulates code chunks
- Frontend infers code completion from event patterns:
  - When `code` events stop and a different event type arrives (e.g., `data` event)
  - When stream closes (all events sent)
- Frontend tracks readiness independently: `hasCodeChunks` and `dataReady` (from arrival of data event)
- Backend remains stateless - just streams events as they occur from LLM/tools
- Rendering logic:
  - When code is complete but data not ready: render component with loading/placeholder state
  - When both are ready: render component with actual data
  - When there is no UI code yet, render the data as a table by default  -->

## Phase 2: The Sandbox (The "Artifact" UI)

[x] Step 3: Sandbox Component

Install react-runner in the frontend.

Create a Preview component that takes a string of code and renders it inside an Error Boundary on the right side of the frontend chat. Test with the sample code returned from backend which is introduced in 2.1

[x] Step 3.1: Render generated data and code together

Update the sample code to be a simple Bar chart and the sample data to be a simple 2-column table of sales and regions; then make sure the generated UI can render the data accordingly

[ ] Step 4: The Parser Utility

Write a utility to extract code blocks from the AI's markdown response (e.g., extracting content between ```tsx blocks).

Connect the Parser to the Preview window so code appears as it streams.

## Phase 3: Data Integration (The "Agent" Logic)

[ ] Step 5.1: Backend Tool Definitions

Define Pydantic models for tools:

- `RunSQLTool`: `query: str`, `limit: int = 1000`, `data_source: Literal["duckdb"]`
- `QueryResult`: `columns: List[str]`, `rows: List[List[Any]]`, `row_count: int`

Implement tool functions:

- `run_sql(query, limit)` - Execute SQL and return `QueryResult` with columns and rows
- Tool returns `QueryResult` Pydantic model
- All queries are assumed to return small result sets (streamed directly in SSE)

Register tools with PydanticAI agent:

- Define tool schemas using Pydantic models
- Create tool implementations that call actual data APIs
- Add tool descriptions for LLM to understand when to use each

## Phase 3 End-to-end integration

[ ] Step 5.2 end-to-end integration with mock

Go through all components with mock data as a tracer bullet:

1. Simulates chat messages without the LLM client
2. Simulate LLM response that contains SQL code block and tool call and query output
3. Simulate LLM response that generates mock UI code
4. Simulate frontend rendering of the mock UI and mock data

[ ] Step 5.3: The LLM Client

- Implements the LLM client using PydanticAI with the tools and connects it with the /chat endpoint
- Create the "Base System Prompt" in FastAPI that instructs the LLM how to call the data tool and how to write code that uses the data prop.

[ ] Step 5.4: Real integration test

Connects the LLM client with everything and simulate a real user interaction - translate prompt into SQL, run tool call, generate UI code, and renders.

## Phase 3.1: Security

[ ] Step 6.1: Security Measures for Code Execution

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

- Data is cached in frontend state for 5 minutes, allow manual refresh
- Store cache keys in frontend state for refresh requests

[ ] Step 8: Template Saving

Setup a simple SQLite or Supabase table to save "Templates" (The original prompt + the generated SQL + the generated UI code).

[ ] Step 8.1: Frontend State Management

Design state architecture:

- Chat messages: Array of `{ role: "user" | "assistant", content: string, timestamp }`
- Active artifact: `{ code: string, codeComplete: boolean, data: QueryResult | null, dataReady: boolean, params: object }`
- Conversation history: Array of previous artifacts/messages
- Loading states: `{ isGenerating: boolean, stage: string }`
- Frontend controls rendering readiness by tracking `codeComplete` and `dataReady` independently

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
