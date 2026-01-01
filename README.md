# Interactive Data Viz Orchestrator

A Claude Artifacts-style application for interactive data visualization using Next.js and FastAPI.

## Project Structure

```
├── frontend/          # Next.js application
├── backend/           # FastAPI application
├── docs/              # Architecture and documentation
└── docker-compose.yml # Docker orchestration
```

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Node.js 20+ (for local frontend development)
- Python 3.11+ (for local backend development)

### Running with Docker Compose

1. Start all services:
```bash
docker-compose up
```

2. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Postgres: localhost:5432

### Local Development

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

#### Backend

Using uv (recommended):
```bash
cd backend
# Install uv if you haven't: curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync  # Installs dependencies from pyproject.toml
uvicorn main:app --reload
```

Or using pip:
```bash
cd backend
pip install -e .
uvicorn main:app --reload
```

#### Environment Variables (Backend)

For LLM agent functionality (Step 4+), configure AWS credentials:

```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=us-east-1  # Optional, defaults to us-east-1
export BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0  # Optional
export USE_LLM_AGENT=true  # Set to false to use word-matching fallback
```

Or use AWS credentials file (`~/.aws/credentials`) or IAM role (if running on EC2).

If AWS credentials are not configured, the backend will automatically fall back to word-matching mode for testing.

## Architecture

See `docs/architecture.md` for detailed architecture documentation.

## Implementation Status

See `docs/implementation_plan.md` for the current implementation status.

