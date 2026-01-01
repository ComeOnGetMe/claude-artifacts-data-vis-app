"""
LLM Client using PydanticAI with Amazon Bedrock
"""
import os
from typing import AsyncIterator, Dict, Any
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.bedrock import BedrockConverseModel, BedrockModelSettings
from pydantic_ai.providers.bedrock import BedrockProvider


class AgentResponse(BaseModel):
    """Response model for agent output"""
    content: str
    metadata: Dict[str, Any] = {}


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
   - Use the run_sql() tool to execute queries

2. **UI Code Generation**: Generate React/TypeScript code for data visualizations immediately after determining the SQL query structure.
   - Analyze the expected data structure from the SQL query (column names, types, aggregation patterns)
   - Generate UI code BEFORE waiting for query execution results
   - Include loading/placeholder states in the generated component
   - Use the expected data structure to create appropriate visualizations

## UI Code Requirements:

### Allowed Libraries (ONLY use these):
- **Recharts**: For charts (BarChart, LineChart, PieChart, AreaChart, ScatterChart, ComposedChart)
- **Shadcn UI**: For layout (Card, CardHeader, CardTitle, CardContent, Table, Badge, Alert, Progress, Skeleton, Button, Slider, Switch, Tabs)
- **Lucide React**: For icons (TrendingUp, AlertCircle, Database, Download, etc.)
- **Tailwind CSS**: For styling

### Component Contract:
Your generated component MUST follow this exact structure:

```tsx
import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip } from 'recharts';

/**
 * @param {Array} data - The dataset returned from the Python backend
 * @param {Object} params - User-defined parameters for customization (optional)
 */
export default function GeneratedViz({ data, params }) {
  if (!data || data.length === 0) {
    return <div className="p-4 text-center">No data available to visualize.</div>;
  }

  // Transform data if needed (backend returns {columns: [], rows: []})
  // Convert to array of objects for Recharts
  const chartData = data.rows.map(row => {
    const obj = {};
    data.columns.forEach((col, idx) => {
      obj[col] = row[idx];
    });
    return obj;
  });

  return (
    <Card className="w-full h-full">
      <CardHeader>
        <CardTitle>{params?.title || 'Data Visualization'}</CardTitle>
      </CardHeader>
      <CardContent className="h-[400px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData}>
            {/* Your visualization logic here */}
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
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
3. [Code] Generate React component with BarChart expecting columns: ['region', 'total_sales']
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
    
    # Create agent with system prompt
    agent = Agent(
        model=model,
        system_prompt=get_base_system_prompt(),
    )
    
    return agent


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
        # Accumulate full response text for parsing
        full_response = ""
        
        # Run agent with streaming - run_stream returns a context manager
        async with agent.run_stream(user_message) as stream_result:
            # Stream text chunks as they arrive
            async for chunk in stream_result.stream_text():
                if chunk:
                    full_response += chunk
                    # Yield incremental thought updates as we receive them
                    # (We'll parse code blocks from full_response later)
                    yield {
                        "type": "thought",
                        "content": chunk
                    }
        
        # After streaming completes, parse code blocks from full response
        # This is a simple approach - in production, you might want to parse incrementally
        code_blocks = _extract_code_blocks(full_response)
        for code_block in code_blocks:
            yield {
                "type": "code",
                "language": code_block.get("language", "tsx"),
                "content": code_block.get("content", "")
            }
    
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

