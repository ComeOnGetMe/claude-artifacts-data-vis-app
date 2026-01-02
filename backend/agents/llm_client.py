"""
LLM Client using PydanticAI with Amazon Bedrock
"""
import os
import httpx
from typing import AsyncIterable, AsyncIterator, Dict, Any
from pydantic import BaseModel
from pydantic_ai import Agent, FunctionToolResultEvent, PartDeltaEvent, PartEndEvent, TextPart, TextPartDelta, ToolCallPart, PartStartEvent, AgentStreamEvent
from pydantic_ai.models.bedrock import BedrockConverseModel, BedrockModelSettings
from pydantic_ai.providers.bedrock import BedrockProvider
from models import RunSQLTool, QueryResult


class AgentResponse(BaseModel):
    """Response model for agent output"""
    content: str
    metadata: Dict[str, Any] = {}


async def run_sql(tool: RunSQLTool) -> QueryResult:
    """
    Tool function to execute SQL queries against DuckDB via the /query/local_duckdb endpoint.
    
    This tool executes SQL queries and returns structured results.
    Use this tool when you need to query data from DuckDB tables.
    
    Args:
        tool: RunSQLTool instance with query, limit, and data_source
        
    Returns:
        QueryResult with columns, rows, and row_count
        
    Raises:
        ValueError: If SQL execution fails or HTTP request fails
    """
    # Get base URL from environment or default to localhost:8000
    base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    
    # Apply limit if not already in query (only for SELECT statements)
    final_query = tool.query
    query_upper = tool.query.upper().strip()
    # Only add LIMIT to SELECT queries, not DDL statements (CREATE, DROP, ALTER, etc.)
    if (tool.limit > 0 and 
        "LIMIT" not in query_upper and 
        query_upper.startswith("SELECT")):
        final_query = f"{tool.query.rstrip(';')} LIMIT {tool.limit}"
    
    # Make HTTP request to /query/local_duckdb endpoint
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{base_url}/query/local_duckdb",
                json={"sql": final_query}
            )
            response.raise_for_status()
            result_data = response.json()
            return QueryResult(**result_data)
        except httpx.HTTPStatusError as e:
            # Extract error message from response
            error_detail = "Unknown error"
            try:
                error_data = e.response.json()
                error_detail = error_data.get("detail", str(e))
            except Exception:
                error_detail = str(e)
            raise ValueError(f"SQL execution error: {error_detail}")
        except httpx.RequestError as e:
            raise ValueError(f"Failed to connect to query endpoint: {str(e)}")


def get_base_system_prompt() -> str:
    """
    Base system prompt that instructs the LLM on:
    - How to call data tools (run_sql)
    - How to write UI code that renders data
    - Component registry constraints
    """
    return """You are a data analyst assistant specialized in generating SQL queries and creating data visualizations.

## Your Capabilities:

1. **SQL Query Generation**: When users ask questions about data, analyze their request and determine what SQL query is needed.
   - Translate natural language requests into SQL queries
   - Always include appropriate WHERE clauses and LIMITs (default limit: 1000 rows)
   - Use the run_sql() tool to execute queries against DuckDB
   - The run_sql tool accepts: query (SQL string), limit (max rows, default 1000), data_source (always "duckdb")

2. **UI Code Generation**: Generate React/TypeScript code for data visualizations immediately after determining the SQL query structure.
   - Analyze the expected data structure from the SQL query (column names, types, aggregation patterns)
   - Generate UI code BEFORE waiting for query execution results
   - Include loading/placeholder states in the generated component
   - Use the expected data structure to create appropriate visualizations

## UI Code Requirements:

### Allowed Libraries (ONLY use these):
- **Recharts**: For charts (BarChart, LineChart, PieChart, AreaChart, ScatterChart, ComposedChart)
- **Shadcn UI**: For layout (Table, Alert, Progress, Skeleton, Button, Slider, Switch, Tabs)
- **Lucide React**: For icons (TrendingUp, AlertCircle, Database, Download, etc.)
- **Tailwind CSS**: For styling

### Component Contract:
Your generated component MUST follow this exact structure:

```tsx
import React from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip } from 'recharts';

/**
 * @param {Object} data - The dataset returned from the Python backend
 *   Format: { columns: string[], rows: any[][] }
 *   Example: { columns: ['region', 'sales'], rows: [['North', '1000'], ['South', '2000']] }
 * @param {Object} params - User-defined parameters for customization (optional)
 */
export default function GeneratedViz({ data, params }) {
  // IMPORTANT: data is an object with {rows, columns}, NOT an array
  // Always check data.rows, not data.length
  if (!data || !data.rows || data.rows.length === 0) {
    return <div className="p-4 text-center">No data available to visualize.</div>;
  }

  // Transform data from {columns: [], rows: []} format to array of objects for Recharts
  // IMPORTANT: Convert numeric strings to numbers for proper chart rendering
  const chartData = data.rows.map(row => {
    const obj = {};
    data.columns.forEach((col, idx) => {
      const value = row[idx];
      // Convert string numbers to actual numbers (e.g., "1000" -> 1000)
      // This is critical for Recharts to render numeric values correctly
      if (typeof value === 'string' && !isNaN(parseFloat(value)) && isFinite(value)) {
        obj[col] = parseFloat(value);
      } else {
        obj[col] = value; // Keep non-numeric strings and already-numeric values as-is
      }
    });
    return obj;
  });

  return (
    <div className="w-full h-full p-4">
      <div className="mb-4">
        <h2 className="text-xl font-semibold">{params?.title || 'Data Visualization'}</h2>
      </div>
      <div className="h-[400px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData}>
            {/* Your visualization logic here */}
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
```

### Prohibited Practices:
- NO external API calls (fetch, axios, etc.)
- NO localStorage or sessionStorage
- NO eval() or dangerous code patterns
- NO libraries outside the allowed list above

## Response Format:

When generating UI code, wrap it in markdown code blocks:
```tsx
// Your component code here
```

When generating SQL queries, you can describe them or use the run_sql() tool.

## Example Workflow:

User: "Show me sales by region for Q1 2024"

Your response:
1. [Thought] "I need to query sales data grouped by region for Q1 2024. I'll generate a SQL query and create a bar chart visualization."
2. [SQL] "SELECT region, SUM(amount) as total_sales FROM sales WHERE date >= '2024-01-01' AND date < '2024-04-01' GROUP BY region ORDER BY total_sales DESC"
3. [Code] Generate React component with BarChart expecting data format:
   - columns: ['region', 'total_sales']
   - rows: [['North', '50000'], ['South', '75000'], ...]
   - Component must check: `if (!data || !data.rows || data.rows.length === 0)`
   - Component must convert numeric strings to numbers in the transformation step
"""


def create_agent() -> Agent:
    """
    Create a PydanticAI agent with Amazon Bedrock model.
    
    Requires AWS credentials configured via:
    - Environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION
    - Or AWS credentials file: ~/.aws/credentials
    - Or IAM role (if running on EC2)
    """
    # Get AWS region from environment or default to us-west-2
    aws_region = os.getenv("AWS_REGION", "us-west-2")
    
    # Get model ID from environment or default to Claude 3.5 Sonnet
    # Common Bedrock model IDs:
    # - anthropic.claude-3-5-sonnet-20241022-v2:0
    # - anthropic.claude-3-opus-20240229-v1:0
    # - anthropic.claude-3-haiku-20240307-v1:0
    model_name = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0")
    
    # Create Bedrock provider with region_name
    # BedrockProvider handles AWS credentials automatically via boto3
    # It will use AWS credentials from environment, credentials file, or IAM role
    bedrock_provider = BedrockProvider(region_name=aws_region)
    
    # Create Bedrock model with settings
    model_settings = BedrockModelSettings(
        temperature=0.7,
        max_tokens=4096,
    )
    
    # Create Bedrock model with the provider
    model = BedrockConverseModel(
        model_name=model_name,
        provider=bedrock_provider,
        settings=model_settings
    )
    
    # Create agent with system prompt and tools
    agent = Agent(
        model=model,
        system_prompt=get_base_system_prompt(),
        tools=[run_sql],
    )
    
    return agent


async def handle_agent_events(event_stream: AsyncIterable[AgentStreamEvent]) -> AsyncIterator[Dict[str, Any]]:
    thought_buffer = ""
    async for event in event_stream:
        if isinstance(event, PartStartEvent):
            if isinstance(event.part, TextPart):  # start of thought
                thought_buffer = event.part.content
                yield {
                    "type": "thought",
                    "content": thought_buffer
                }
        elif isinstance(event, PartDeltaEvent):
            if isinstance(event.delta, TextPartDelta):  # continuation of thought
                delta = event.delta.content_delta
                thought_buffer += delta
                yield {
                    "type": "thought",
                    "content": thought_buffer
                }
        elif isinstance(event, FunctionToolResultEvent):  # end of tool call
            tool_result = event.result.content
            if isinstance(tool_result, QueryResult):
                yield {
                    "type": "data",
                    "payload": {
                        "columns": tool_result.columns,
                        "rows": tool_result.rows,
                        "row_count": tool_result.row_count
                    }
                }
        elif isinstance(event, PartEndEvent):
            if isinstance(event.part, TextPart):  # complete thought, parse code blocks
                code_blocks = _extract_code_blocks(event.part.content)
                for code_block in code_blocks:
                    yield {
                        "type": "code",
                        "language": code_block.get("language", "tsx"),
                        "content": code_block.get("content", "")
                    }
            if isinstance(event.part, ToolCallPart):  # complete tool call, notify tool call
                yield {
                    "type": "thought",
                    "content": f"Calling tool: {event.part.tool_name} with args: {event.part.args}"
                }
        # TODO: avoid sending code blocks as thought? 


async def stream_agent_response(agent: Agent, user_message: str) -> AsyncIterator[Dict[str, Any]]:
    """
    Stream agent response and yield events for SSE.
    
    Yields events in the format:
    - {"type": "thought", "content": "..."}
    - {"type": "code", "language": "tsx", "content": "..."}
    - {"type": "data", "payload": {...}}
    - {"type": "error", "message": "..."}
    """
    try:
        # Run agent with streaming - run_stream returns a context manager
        async for event in handle_agent_events(agent.run_stream_events(user_message)):
            yield event

    except Exception as e:
        yield {
            "type": "error",
            "message": str(e),
            "stage": "llm_processing"
        }


def _extract_code_blocks(text: str) -> list[Dict[str, str]]:
    """
    Extract code blocks from markdown text.
    Returns list of dicts with 'language' and 'content' keys.
    """
    import re
    
    code_blocks = []
    # Pattern to match ```language\ncontent\n```
    # Handles cases with or without language specifier
    # Also handles code blocks that might not start immediately after ```
    pattern = r'```(\w+)?\s*\n(.*?)```'
    
    matches = re.finditer(pattern, text, re.DOTALL)
    for match in matches:
        language = match.group(1) or "tsx"
        content = match.group(2).strip()
        if content:
            code_blocks.append({
                "language": language,
                "content": content
            })
    
    return code_blocks

