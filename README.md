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
uv pip install -r requirements.txt
uvicorn main:app --reload
```

Or using pip:
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

## Architecture

See `docs/architecture.md` for detailed architecture documentation.

## Implementation Status

See `docs/implementation_plan.md` for the current implementation status.

