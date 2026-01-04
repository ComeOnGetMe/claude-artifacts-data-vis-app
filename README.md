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

This project follows Docker Compose best practices with separate configurations for development and production:

- **`docker-compose.yml`** - Base configuration (common settings)
- **`docker-compose.override.yml`** - Development overrides (auto-loaded)
- **`docker-compose.prod.yml`** - Production overrides

#### Development Mode (default)
For local development with live reloading, simply run:
```bash
docker-compose up --build
```

The `docker-compose.override.yml` file is automatically loaded, which:
- Uses `Dockerfile.dev` for both services
- Mounts source code as volumes for real-time changes
- Enables hot reloading

**Note**: Code changes are reflected immediately without restarting containers.

#### Production Mode
For production deployment:
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build
```

Production mode:
- Uses regular `Dockerfile` (code is copied into image)
- No volume mounts (code is baked into image)
- Uses production commands (`npm run start` instead of `npm run dev`)
- Includes restart policies

#### Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Postgres: localhost:5432

#### Environment Variables
Create a `.env` file in the project root to customize settings:
```bash
# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=vizdb
POSTGRES_PORT=5432

# Backend
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000

# Frontend
FRONTEND_PORT=3000
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Docker Compose automatically reads environment variables from:
- Your shell environment
- A `.env` file in the same directory as `docker-compose.yml`
- Variables passed inline with the command

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
uv run uvicorn main:app --reload
```

#### Environment Variables (Backend)

For LLM agent functionality (Step 4+), configure AWS credentials:

```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=us-east-1  # Optional, defaults to us-east-1
export BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0  # Optional
```

Or use AWS credentials file (`~/.aws/credentials`) or IAM role (if running on EC2).

If AWS credentials are not configured, the backend will automatically fall back to word-matching mode for testing.

## Architecture

See `docs/architecture.md` for detailed architecture documentation.

## Implementation Status

See `docs/implementation_plan.md` for the current implementation status.

